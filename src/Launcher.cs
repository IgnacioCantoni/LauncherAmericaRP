// Launcher de AMERICA RP. Escrito en C# 5 para que compile con el csc que ya trae Windows
// (.NET Framework 4.x) y con mcs de Mono. Ver README.md.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Security.Cryptography;
using System.Text;
using System.IO.Compression;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using System.Windows.Forms;
using Microsoft.Win32;

static class Config
{
    // Lo que cambia de un server a otro. Después de tocarlo, volvé a compilar.
    public const string Host = "127.0.0.1";
    public const int Puerto = 7777;
    // Vacío = sin noticias / sin actualizaciones.
    const string Repo = "https://raw.githubusercontent.com/IgnacioCantoni/LauncherAmericaRP/main/";
    public const string NoticiasUrl = Repo + "noticias.txt";
    public const string ManifiestoUrl = Repo + "actualizaciones/manifiesto.txt";
    // GTA Full: gráficos ENB, opcionales (se activan en MI JUEGO). La licencia de ENBSeries no deja repartir su d3d9.dll
    // por un launcher: cada jugador baja el zip oficial y el launcher lo instala desde ahí. Lo que sí se reparte es el
    // preset del server (.ini y .fx) en paquetes/enb. EnbUrl vacío = no aparece.
    public const string EnbUrl = Repo + "paquetes/enb/manifiesto.txt";
    public const string EnbDescargaUrl = "http://enbdev.com/download_mod_gtasa.htm";
    public const string EnbZip = "enbseries_gtasa_v0430.zip";
    // Con SA-MP 0.3.7 la versión d3d9.dll del ENB cierra el juego: se usa la versión ASI (AsiVersion/enbseries.asi),
    // que carga el Ultimate ASI Loader (dinput8.dll, licencia MIT). El cargador va en actualizaciones porque también lo usa CLEO.
    public const string EnbAsiSha = "a166b48a3eec747a38ac512b23003cb244134aacb9c18ace67baaca7188c64b1"; // enbseries.asi de la v0.430
    public const string AsiLoaderSha = "63b465dbc1bf9c5ab4e33c3ccad099d9edb702f2c51587ac8d4f196497396437"; // dinput8.dll que va en actualizaciones
    public const string DescargaSampUrl = "https://www.sa-mp.mp/downloads/";
    // Links del pie de la ventana, en este orden. Los que tengan el link vacío no aparecen.
    public static readonly KeyValuePair<string, string>[] Redes =
    {
        new KeyValuePair<string, string>("Discord", ""),
        new KeyValuePair<string, string>("YouTube", ""),
        new KeyValuePair<string, string>("TikTok", ""),
        new KeyValuePair<string, string>("Instagram", ""),
        new KeyValuePair<string, string>("Soporte", ""),
    };
}

class EstadoServidor
{
    public bool EnLinea;
    public string Nombre = "";
    public int Jugadores, Maximo;
    public long Ping;
}

// Protocolo de consulta de SA-MP (open.mp lo responde igual): paquete "i" = información.
static class Consulta
{
    public static EstadoServidor Pedir(string host, int puerto, int esperaMs)
    {
        try
        {
            IPAddress ip = Resolver(host);
            byte[] pedido = ArmarPedido(ip, puerto, (byte)'i');
            using (var udp = new UdpClient())
            {
                udp.Client.ReceiveTimeout = esperaMs;
                udp.Connect(ip, puerto);
                var reloj = Stopwatch.StartNew();
                udp.Send(pedido, pedido.Length);
                IPEndPoint remoto = null;
                byte[] respuesta = udp.Receive(ref remoto);
                EstadoServidor e = Leer(respuesta);
                e.Ping = reloj.ElapsedMilliseconds;
                return e;
            }
        }
        catch (Exception)
        {
            // Sin respuesta, puerto cerrado o DNS caído: para el jugador es lo mismo, el server no está.
            return new EstadoServidor();
        }
    }

    static IPAddress Resolver(string host)
    {
        IPAddress ip;
        if (IPAddress.TryParse(host, out ip)) return ip;
        return Dns.GetHostAddresses(host).First(a => a.AddressFamily == AddressFamily.InterNetwork);
    }

    public static byte[] ArmarPedido(IPAddress ip, int puerto, byte opcode)
    {
        var p = new List<byte>(Encoding.ASCII.GetBytes("SAMP"));
        p.AddRange(ip.GetAddressBytes());
        p.Add((byte)(puerto & 0xFF));
        p.Add((byte)(puerto >> 8));
        p.Add(opcode);
        return p.ToArray();
    }

    // La respuesta viene del exterior: cada largo se revisa antes de leer.
    public static EstadoServidor Leer(byte[] r)
    {
        var e = new EstadoServidor();
        if (r == null || r.Length < 11 + 5 || Encoding.ASCII.GetString(r, 0, 4) != "SAMP" || r[10] != 'i') return e;
        int pos = 12; // 11 = tiene contraseña
        e.Jugadores = BitConverter.ToUInt16(r, pos); pos += 2;
        e.Maximo = BitConverter.ToUInt16(r, pos); pos += 2;
        if (pos + 4 <= r.Length)
        {
            int largo = BitConverter.ToInt32(r, pos); pos += 4;
            if (largo > 0 && pos + largo <= r.Length) e.Nombre = Texto1252().GetString(r, pos, largo);
        }
        e.EnLinea = true;
        return e;
    }

    public static Encoding Texto1252()
    {
        try { return Encoding.GetEncoding(1252); }
        catch (Exception) { return Encoding.GetEncoding(28591); }
    }
}

// Datos que el cliente SA-MP ya guarda en el registro: los usamos para que el nick y la carpeta sean los mismos.
static class Registro
{
    const string Clave = @"Software\SAMP";

    static string Leer(string valor)
    {
        using (RegistryKey k = Registry.CurrentUser.OpenSubKey(Clave))
        {
            object v = k == null ? null : k.GetValue(valor);
            return v == null ? "" : v.ToString();
        }
    }

    static void Guardar(string valor, string dato)
    {
        using (RegistryKey k = Registry.CurrentUser.CreateSubKey(Clave)) k.SetValue(valor, dato);
    }

    public static string Nick { get { return Leer("PlayerName"); } set { Guardar("PlayerName", value); } }
    public static string GtaExe { get { return Leer("gta_sa_exe"); } set { Guardar("gta_sa_exe", value); } }
}

static class Instalacion
{
    // shortcut: solo tamaños conocidos de gta_sa.exe 1.0; si el tuyo es 1.0 y avisa, sumá su tamaño acá.
    public static readonly long[] TamanosGta10 = { 14383616, 5189632 };

    public static readonly Regex NickValido = new Regex(@"^[A-Za-z0-9_\[\]\.\$@=\(\)]{3,20}$");

    // Problemas que impiden jugar. El aviso de versión va aparte porque no bloquea.
    public static List<string> Faltantes(string carpeta)
    {
        var lista = new List<string>();
        if (string.IsNullOrEmpty(carpeta) || !File.Exists(Path.Combine(carpeta, "gta_sa.exe")))
        {
            lista.Add("No se encontró gta_sa.exe. Elegí la carpeta del GTA San Andreas.");
            return lista;
        }
        if (!File.Exists(Path.Combine(carpeta, "samp.exe")) || !File.Exists(Path.Combine(carpeta, "samp.dll")))
            lista.Add("Falta el cliente SA-MP 0.3.7 en la carpeta del GTA.");
        return lista;
    }

    public static bool PareceGta10(string carpeta)
    {
        long tam = new FileInfo(Path.Combine(carpeta, "gta_sa.exe")).Length;
        return TamanosGta10.Contains(tam);
    }
}

// Actualizaciones: un manifiesto con "sha256 ruta" por línea; cada archivo está en archivos/<ruta> junto al manifiesto.
static class Actualizador
{
    public const string NombreManifiesto = "manifiesto.txt";
    static readonly Regex Linea = new Regex(@"^([0-9a-f]{64}) (.+)$");

    public static List<KeyValuePair<string, string>> LeerManifiesto(string texto)
    {
        var entradas = new List<KeyValuePair<string, string>>();
        foreach (string cruda in texto.Replace("\r", "").Split('\n'))
        {
            string l = cruda.Trim();
            if (l.Length == 0 || l.StartsWith("#")) continue;
            Match m = Linea.Match(l);
            if (!m.Success) throw new InvalidDataException("Línea inválida en el manifiesto: " + l);
            entradas.Add(new KeyValuePair<string, string>(m.Groups[1].Value, m.Groups[2].Value));
        }
        return entradas;
    }

    // El manifiesto viene de internet: ninguna ruta puede salir de la carpeta del GTA.
    public static string RutaSegura(string carpeta, string ruta)
    {
        if (ruta.Contains(":") || ruta.StartsWith("/") || ruta.StartsWith("\\") || ruta.Split('/', '\\').Contains(".."))
            throw new InvalidDataException("Ruta no permitida en el manifiesto: " + ruta);
        string raiz = Path.GetFullPath(carpeta).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        string destino = Path.GetFullPath(Path.Combine(raiz, ruta.Replace('/', Path.DirectorySeparatorChar)));
        if (!destino.StartsWith(raiz, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("Ruta no permitida en el manifiesto: " + ruta);
        return destino;
    }

    public static string UrlArchivo(string manifiestoUrl, string ruta)
    {
        string baseUrl = manifiestoUrl.Substring(0, manifiestoUrl.LastIndexOf('/') + 1);
        return baseUrl + "archivos/" + string.Join("/", ruta.Split('/').Select(Uri.EscapeDataString));
    }

    public static string Sha256(string archivo)
    {
        using (var sha = SHA256.Create())
        using (FileStream f = File.OpenRead(archivo))
            return BitConverter.ToString(sha.ComputeHash(f)).Replace("-", "").ToLowerInvariant();
    }

    public static string GenerarManifiesto(string carpetaArchivos)
    {
        string raiz = Path.GetFullPath(carpetaArchivos).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        var sb = new StringBuilder("# Generado por AmericaRP.exe --manifiesto. No editar a mano.\n");
        foreach (string archivo in Directory.GetFiles(raiz, "*", SearchOption.AllDirectories).OrderBy(a => a, StringComparer.Ordinal))
            sb.Append(Sha256(archivo)).Append(' ').Append(archivo.Substring(raiz.Length).Replace('\\', '/')).Append('\n');
        return sb.ToString();
    }

    public class Revision
    {
        public List<KeyValuePair<string, string>> Entradas = new List<KeyValuePair<string, string>>();
        public HashSet<string> Pendientes = new HashSet<string>();
        public string Texto = "";
    }

    // Baja el manifiesto y marca qué archivos el jugador no tiene o tiene distintos.
    public static Revision Revisar(string carpetaGta, string manifiestoUrl, Action<string, int> progreso)
    {
        var r = new Revision();
        progreso("Buscando actualizaciones...", 0);
        using (var web = new WebClient())
        {
            web.Encoding = Encoding.UTF8;
            r.Texto = web.DownloadString(manifiestoUrl);
            r.Entradas = LeerManifiesto(r.Texto);
        }
        for (int i = 0; i < r.Entradas.Count; i++)
        {
            string destino = RutaSegura(carpetaGta, r.Entradas[i].Value);
            progreso("Revisando " + r.Entradas[i].Value, 100 * i / Math.Max(1, r.Entradas.Count));
            if (!File.Exists(destino) || Sha256(destino) != r.Entradas[i].Key) r.Pendientes.Add(r.Entradas[i].Value);
        }
        return r;
    }

    // Una línea "sha256 ruta" por cada ruta que exista en la carpeta: sirve para recordar qué se instaló.
    public static string Huellas(string carpetaGta, IEnumerable<string> rutas)
    {
        var sb = new StringBuilder();
        foreach (string ruta in rutas.Distinct().OrderBy(r => r, StringComparer.Ordinal))
        {
            string destino = RutaSegura(carpetaGta, ruta);
            if (File.Exists(destino)) sb.Append(Sha256(destino)).Append(' ').Append(ruta).Append('\n');
        }
        return sb.ToString();
    }

    static string Sha256(Stream s)
    {
        using (var sha = SHA256.Create()) return BitConverter.ToString(sha.ComputeHash(s)).Replace("-", "").ToLowerInvariant();
    }

    // Instala la versión ASI del zip oficial de ENBSeries que bajó el jugador: AsiVersion/enbseries.asi más los ajustes y
    // shaders de WrapperVersion, menos su d3d9.dll. Antes de copiar nada revisa que sea la versión esperada y que no pise
    // archivos de otro mod. Devuelve las rutas instaladas.
    public static List<string> InstalarZipEnb(string carpetaGta, string zip, string asiSha)
    {
        using (ZipArchive z = ZipFile.OpenRead(zip))
        {
            var archivos = new List<KeyValuePair<string, ZipArchiveEntry>>();
            foreach (ZipArchiveEntry e in z.Entries)
            {
                string nombre = e.FullName.Replace('\\', '/');
                if (e.Name.Length == 0) continue;
                if (nombre == "AsiVersion/enbseries.asi") archivos.Add(new KeyValuePair<string, ZipArchiveEntry>("enbseries.asi", e));
                else if (nombre.StartsWith("WrapperVersion/") && nombre != "WrapperVersion/d3d9.dll")
                    archivos.Add(new KeyValuePair<string, ZipArchiveEntry>(nombre.Substring("WrapperVersion/".Length), e));
            }
            ZipArchiveEntry asi = archivos.Where(a => a.Key == "enbseries.asi").Select(a => a.Value).FirstOrDefault();
            if (asi == null) throw new InvalidDataException("Ese zip no es el ENBSeries para GTA San Andreas.");
            using (Stream s = asi.Open())
                if (Sha256(s) != asiSha) throw new InvalidDataException("Ese zip es otra versión del ENB. El server usa la del archivo " + Config.EnbZip + ".");
            string loader = RutaSegura(carpetaGta, "dinput8.dll");
            if (File.Exists(loader) && Sha256(loader) != Config.AsiLoaderSha)
                throw new InvalidDataException("Tu GTA ya tiene un dinput8.dll de otro mod. Sacalo antes de activar el ENB.");
            foreach (KeyValuePair<string, ZipArchiveEntry> a in archivos)
            {
                string destino = RutaSegura(carpetaGta, a.Key);
                if (File.Exists(destino)) using (Stream s = a.Value.Open()) if (Sha256(destino) != Sha256(s))
                    throw new InvalidDataException("Tu GTA ya tiene un " + a.Key + " de otro mod. Sacalo antes de activar el ENB.");
            }
            foreach (KeyValuePair<string, ZipArchiveEntry> a in archivos)
            {
                string destino = RutaSegura(carpetaGta, a.Key);
                Directory.CreateDirectory(Path.GetDirectoryName(destino));
                a.Value.ExtractToFile(destino, true);
            }
            return archivos.Select(a => a.Key).ToList();
        }
    }

    // Saca de la carpeta del GTA los archivos de un manifiesto que se instaló antes. Solo borra los que siguen
    // idénticos a los instalados: si el jugador puso su propio archivo con el mismo nombre, no se toca.
    public static int Quitar(string carpetaGta, string textoManifiesto)
    {
        int borrados = 0;
        foreach (KeyValuePair<string, string> e in LeerManifiesto(textoManifiesto))
        {
            string destino = RutaSegura(carpetaGta, e.Value);
            if (File.Exists(destino) && Sha256(destino) == e.Key) { File.Delete(destino); borrados++; }
        }
        return borrados;
    }

    // Devuelve lo que revisó; en Pendientes queda lo que bajó. Si algo falla, tira la excepción y no deja archivos a medias.
    public static Revision Aplicar(string carpetaGta, string manifiestoUrl, Action<string, int> progreso)
    {
        Revision r = Revisar(carpetaGta, manifiestoUrl, progreso);
        var pendientes = r.Entradas.Where(e => r.Pendientes.Contains(e.Value)).ToList();
        using (var web = new WebClient())
        {
            for (int i = 0; i < pendientes.Count; i++)
            {
                string ruta = pendientes[i].Value, destino = RutaSegura(carpetaGta, ruta), temporal = destino + ".descarga";
                progreso("Bajando " + ruta + " (" + (i + 1) + " de " + pendientes.Count + ")", 100 * i / pendientes.Count);
                Directory.CreateDirectory(Path.GetDirectoryName(destino));
                try
                {
                    web.DownloadFile(UrlArchivo(manifiestoUrl, ruta), temporal);
                    if (Sha256(temporal) != pendientes[i].Key)
                        throw new InvalidDataException("El archivo bajado no coincide con el manifiesto: " + ruta);
                    try { File.Copy(temporal, destino, true); }
                    catch (IOException) { throw new IOException("No se pudo reemplazar " + ruta + ". Cerrá el GTA y probá de nuevo."); }
                }
                finally
                {
                    if (File.Exists(temporal)) File.Delete(temporal);
                }
            }
        }
        progreso(pendientes.Count == 0 ? "Todo al día." : "Actualizado: " + pendientes.Count + " archivo(s).", 100);
        return r;
    }
}

// Tipografías propias (SIL OFL, ver fuentes/): Montserrat Bold Italic para títulos (la del video) y Barlow para el resto.
// Van dentro del .exe como recursos; si no cargan, se usa Segoe UI.
static class Fuentes
{
    static readonly System.Drawing.Text.PrivateFontCollection coleccion = new System.Drawing.Text.PrivateFontCollection();
    static readonly Dictionary<string, Font> cache = new Dictionary<string, Font>();
    static FontFamily titulo, cuerpo;

    static Fuentes()
    {
        foreach (string nombre in new[] { "Montserrat-BoldItalic.ttf", "Barlow-Regular.ttf", "Barlow-Bold.ttf" })
        {
            try
            {
                // Se copian a un archivo porque las fuentes cargadas desde memoria no se dibujan en todos lados (Mono, algunos Windows).
                string destino = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "AmericaRP", "fuentes", nombre);
                using (Stream s = typeof(Fuentes).Assembly.GetManifestResourceStream(nombre))
                {
                    if (s == null) continue;
                    if (!File.Exists(destino) || new FileInfo(destino).Length != s.Length)
                    {
                        Directory.CreateDirectory(Path.GetDirectoryName(destino));
                        using (FileStream f = File.Create(destino)) s.CopyTo(f);
                    }
                }
                coleccion.AddFontFile(destino);
            }
            catch (Exception) { }
        }
        foreach (FontFamily f in coleccion.Families)
        {
            if (f.Name == "Montserrat") titulo = f;
            if (f.Name == "Barlow") cuerpo = f;
        }
    }

    static Font Pedir(FontFamily fam, float tam, FontStyle estilo)
    {
        string clave = (fam == null ? "segoe" : fam.Name) + tam + estilo;
        Font f;
        if (!cache.TryGetValue(clave, out f))
        {
            // En Mono las fuentes privadas salen como cuadrados: ahí se piden por nombre (tienen que estar instaladas).
            if (fam != null && Type.GetType("Mono.Runtime") != null) f = new Font(fam.Name, tam, estilo);
            else f = fam != null && fam.IsStyleAvailable(estilo) ? new Font(fam, tam, estilo, GraphicsUnit.Point) : new Font("Segoe UI", tam * (fam == titulo ? 0.8f : 1f), estilo | (fam == titulo ? FontStyle.Bold : 0));
            cache[clave] = f;
        }
        return f;
    }

    // Los tamaños de la interfaz se pensaron para una letra angosta; Montserrat es más ancha, así que se achica acá.
    public static Font Titulo(float tam) { return Pedir(titulo, tam * 0.6f, FontStyle.Bold | FontStyle.Italic); }
    public static Font Texto(float tam) { return Pedir(cuerpo, tam, FontStyle.Regular); }
    public static Font Negrita(float tam) { return Pedir(cuerpo, tam, FontStyle.Bold); }
}

// La ventana se dibuja entera a mano (sin bordes de Windows) y se repinta ~30 veces por segundo por el fondo animado.
// Los botones son zonas: cada vez que se pinta se anotan su rectángulo y su acción.
class Ventana : Form
{
    static readonly Color Acento = Color.FromArgb(245, 166, 35), Texto = Color.FromArgb(244, 241, 234), Gris = Color.FromArgb(168, 172, 186),
        Oscuro = Color.FromArgb(8, 10, 16), Verde = Color.FromArgb(110, 220, 140), Rojo = Color.FromArgb(240, 96, 96), Ambar = Color.FromArgb(245, 196, 80);
    const int Ancho = 1100, Alto = 660;
    static readonly Rectangle Tarjeta = new Rectangle(744, 92, 316, 520), Contenido = new Rectangle(40, 92, 672, 520);

    class Zona { public Rectangle R; public Action Click; }
    readonly List<Zona> zonas = new List<Zona>();
    readonly TextBox nick = new TextBox();
    readonly Timer reloj = new Timer(), cuadros = new Timer();
    readonly Stopwatch tiempo = Stopwatch.StartNew();
    readonly Video video = Video.Cargar();
    Point mouse = new Point(-1, -1), arrastre;
    bool arrastrando, consultando, ocupado;

    EstadoServidor server = new EstadoServidor();
    bool serverConsultado;
    string pestana = "inicio", noticias = "Cargando noticias...", estado = "Listo para jugar.", mods = "";
    int progreso, scroll;
    Actualizador.Revision revision;
    List<string> faltantes = new List<string>();
    bool gta10;

    public Ventana()
    {
        Text = "AMERICA RP";
        FormBorderStyle = FormBorderStyle.None;
        ClientSize = new Size(Ancho, Alto);
        StartPosition = FormStartPosition.CenterScreen;
        BackColor = Oscuro;
        DoubleBuffered = true;
        SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.UserPaint | ControlStyles.OptimizedDoubleBuffer, true);
        try { Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath); } catch (Exception) { }

        nick.BorderStyle = BorderStyle.None;
        nick.BackColor = Color.FromArgb(20, 22, 30);
        nick.ForeColor = Texto;
        nick.Font = new Font("Segoe UI", 13f, FontStyle.Bold);
        nick.MaxLength = 20;
        nick.SetBounds(Tarjeta.X + 36, Tarjeta.Y + 262, Tarjeta.Width - 72, 26);
        nick.Text = Registro.Nick;
        nick.TextChanged += delegate { Invalidate(); };
        Controls.Add(nick);

        RevisarInstalacion();
        reloj.Interval = 15000;
        reloj.Tick += delegate { RefrescarServer(); };
        cuadros.Interval = 33;
        cuadros.Tick += delegate { if (WindowState != FormWindowState.Minimized) Invalidate(); };
        Shown += delegate
        {
            ActiveControl = nick;
            nick.SelectionStart = nick.Text.Length;
            reloj.Start();
            cuadros.Start();
            RefrescarServer();
            CargarNoticias();
            RevisarMods();
        };
    }

    // ---------- datos ----------

    string Carpeta()
    {
        string exe = Registro.GtaExe;
        return exe.Length == 0 ? "" : Path.GetDirectoryName(exe);
    }

    void RevisarInstalacion()
    {
        faltantes = Instalacion.Faltantes(Carpeta());
        gta10 = File.Exists(Path.Combine(Carpeta(), "gta_sa.exe")) && Instalacion.PareceGta10(Carpeta());
    }

    void Avisar(string texto, int porcentaje)
    {
        if (InvokeRequired) { BeginInvoke(new Action<string, int>(Avisar), texto, porcentaje); return; }
        estado = texto;
        progreso = Math.Max(0, Math.Min(100, porcentaje));
    }

    async void RefrescarServer()
    {
        if (consultando) return;
        consultando = true;
        server = await Task.Run(() => Consulta.Pedir(Config.Host, Config.Puerto, 2500));
        serverConsultado = true;
        consultando = false;
    }

    async void CargarNoticias()
    {
        if (Config.NoticiasUrl.Length == 0) { noticias = "Todavía no hay noticias."; return; }
        try { noticias = await Task.Run(() => Web.Texto(Config.NoticiasUrl)); }
        catch (Exception ex) { noticias = "No se pudieron cargar las noticias: " + ex.Message; }
    }

    async void RevisarMods()
    {
        if (Config.ManifiestoUrl.Length == 0) { mods = "Este server no reparte archivos propios."; return; }
        if (Carpeta().Length == 0) { mods = "Elegí la carpeta del GTA para ver tus archivos."; return; }
        string carpeta = Carpeta();
        try
        {
            revision = await Task.Run(() => Actualizador.Revisar(carpeta, Config.ManifiestoUrl, delegate { }));
            mods = revision.Entradas.Count == 0 ? "Todavía no hay mods ni archivos del server." : "";
        }
        catch (Exception ex) { revision = null; mods = "No se pudieron revisar los archivos: " + ex.Message; }
    }

    // ---------- acciones ----------

    bool ElegirCarpeta()
    {
        using (var d = new OpenFileDialog { Title = "Buscá gta_sa.exe", Filter = "GTA San Andreas|gta_sa.exe" })
        {
            if (d.ShowDialog(this) != DialogResult.OK) return false;
            Registro.GtaExe = d.FileName;
        }
        RevisarInstalacion();
        RevisarMods();
        return true;
    }

    void Ocupar(bool si)
    {
        ocupado = si;
        nick.Enabled = !si;
    }

    // Baja lo que cambió (si hay manifiesto) y dice qué falta. Devuelve true si se puede jugar.
    async Task<bool> Preparar()
    {
        if (Carpeta().Length == 0 && !ElegirCarpeta()) return false;
        string carpeta = Carpeta();
        if (Config.ManifiestoUrl.Length > 0 && File.Exists(Path.Combine(carpeta, "gta_sa.exe")))
        {
            try { await Task.Run(() => Actualizador.Aplicar(carpeta, Config.ManifiestoUrl, Avisar)); }
            catch (Exception ex)
            {
                Avisar("No se pudo actualizar.", 0);
                RevisarMods();
                if (MessageBox.Show(this, ex.Message + "\n\n¿Seguir sin actualizar?", "Actualizaciones", MessageBoxButtons.YesNo, MessageBoxIcon.Warning) != DialogResult.Yes)
                    return false;
            }
            RevisarMods();
        }
        if (EnbActivo() && Config.EnbUrl.Length > 0 && File.Exists(Path.Combine(carpeta, "gta_sa.exe")))
        {
            // El ENB es opcional: si falla se avisa y se juega igual.
            try
            {
                Actualizador.Revision enb = await Task.Run(() => Actualizador.Aplicar(carpeta, Config.EnbUrl, Avisar));
                // Se recuerda lo del zip más lo del preset, con cómo quedó cada archivo, para poder sacarlo después.
                var rutas = Actualizador.LeerManifiesto(File.ReadAllText(EnbArchivo())).Select(e => e.Value).Concat(enb.Entradas.Select(e => e.Value));
                File.WriteAllText(EnbArchivo(), Actualizador.Huellas(carpeta, rutas));
            }
            catch (Exception ex) { Avisar("No se pudo instalar el ENB: " + ex.Message, 0); }
        }
        RevisarInstalacion();
        if (faltantes.Count > 0)
        {
            Avisar(faltantes[0], 0);
            bool sinSamp = faltantes[0].Contains("SA-MP");
            string pregunta = string.Join("\n", faltantes) + (sinSamp ? "\n\n¿Abrir la página para bajar SA-MP 0.3.7?" : "");
            if (MessageBox.Show(this, pregunta, "Instalación", sinSamp ? MessageBoxButtons.YesNo : MessageBoxButtons.OK, MessageBoxIcon.Warning) == DialogResult.Yes)
                Abrir(Config.DescargaSampUrl);
            return false;
        }
        if (!gta10) Avisar("Tu gta_sa.exe no parece la versión 1.0. Si el juego se cierra al conectar, instalá la 1.0.", 100);
        return true;
    }

    // Si el ENB está activo, este archivo existe y guarda el manifiesto que se instaló, para poder sacarlo después.
    static string EnbArchivo()
    {
        return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "AmericaRP", "enb-instalado.txt");
    }

    static bool EnbActivo() { return File.Exists(EnbArchivo()); }

    async void CambiarEnb()
    {
        if (ocupado) return;
        if (!EnbActivo())
        {
            if (Carpeta().Length == 0 && !ElegirCarpeta()) return;
            string carpeta = Carpeta(), zip;
            MessageBox.Show(this, "El ENB se baja de su página oficial. Se va a abrir: bajá el archivo " + Config.EnbZip +
                " (versión 0.430) y después elegilo en la ventana que aparece.", "Activar ENB", MessageBoxButtons.OK, MessageBoxIcon.Information);
            Abrir(Config.EnbDescargaUrl);
            using (var d = new OpenFileDialog { Title = "Elegí " + Config.EnbZip, Filter = "ENBSeries|*.zip", FileName = Config.EnbZip })
            {
                if (d.ShowDialog(this) != DialogResult.OK) return;
                zip = d.FileName;
            }
            Ocupar(true);
            try
            {
                List<string> rutas = await Task.Run(() => Actualizador.InstalarZipEnb(carpeta, zip, Config.EnbAsiSha));
                Directory.CreateDirectory(Path.GetDirectoryName(EnbArchivo()));
                File.WriteAllText(EnbArchivo(), Actualizador.Huellas(carpeta, rutas));
                Avisar("ENB instalado. Shift+F12 lo prende y lo apaga en el juego.", 100);
            }
            catch (Exception ex) { MessageBox.Show(this, ex.Message, "Activar ENB", MessageBoxButtons.OK, MessageBoxIcon.Warning); return; }
            finally { Ocupar(false); }
            Actualizar(); // suma el preset del server
            return;
        }
        Ocupar(true);
        try
        {
            string carpeta = Carpeta(), texto = File.ReadAllText(EnbArchivo());
            // Los ENB instalados antes de CLEO tienen anotado el dinput8.dll, que ahora se queda porque lo usa CLEO.
            texto = string.Join("\n", texto.Split('\n').Where(l => !l.TrimEnd().EndsWith(" dinput8.dll")));
            int n = carpeta.Length == 0 ? 0 : await Task.Run(() => Actualizador.Quitar(carpeta, texto));
            File.Delete(EnbArchivo());
            Avisar("ENB desactivado: se sacaron " + n + " archivo(s).", 100);
        }
        catch (Exception ex) { Avisar("No se pudo sacar el ENB: " + ex.Message + ". Cerrá el GTA y probá de nuevo.", 0); }
        finally { Ocupar(false); }
    }

    async void Actualizar()
    {
        if (ocupado) return;
        Ocupar(true);
        try { if (await Preparar() && gta10) Avisar("Todo listo para jugar.", 100); }
        finally { Ocupar(false); }
    }

    async void Jugar()
    {
        if (ocupado) return;
        string n = nick.Text.Trim();
        if (!Instalacion.NickValido.IsMatch(n))
        {
            MessageBox.Show(this, "El nick tiene que tener de 3 a 20 caracteres: letras, números o _ [ ] . $ @ = ( )", "Nick", MessageBoxButtons.OK, MessageBoxIcon.Information);
            nick.Focus();
            return;
        }
        Ocupar(true);
        try
        {
            Registro.Nick = n;
            if (!await Preparar()) return;
            string carpeta = Carpeta();
            Process.Start(new ProcessStartInfo(Path.Combine(carpeta, "samp.exe"), Config.Host + ":" + Config.Puerto) { WorkingDirectory = carpeta });
            Avisar("Abriendo el GTA...", 100);
            WindowState = FormWindowState.Minimized;
        }
        catch (Exception ex) { MessageBox.Show(this, "No se pudo abrir el juego: " + ex.Message, "AMERICA RP", MessageBoxButtons.OK, MessageBoxIcon.Error); }
        finally { Ocupar(false); }
    }

    static void Abrir(string url)
    {
        try { Process.Start(url); } catch (Exception) { }
    }

    void Pestana(string p)
    {
        pestana = p;
        scroll = 0;
    }

    // ---------- mouse ----------

    protected override void OnMouseMove(MouseEventArgs e)
    {
        base.OnMouseMove(e);
        if (arrastrando) { Location = new Point(Location.X + e.X - arrastre.X, Location.Y + e.Y - arrastre.Y); return; }
        mouse = e.Location;
        Cursor = ZonaEn(e.Location) != null ? Cursors.Hand : Cursors.Default;
    }

    protected override void OnMouseLeave(EventArgs e)
    {
        base.OnMouseLeave(e);
        mouse = new Point(-1, -1);
    }

    protected override void OnMouseDown(MouseEventArgs e)
    {
        base.OnMouseDown(e);
        if (e.Button == MouseButtons.Left && e.Y < 76 && ZonaEn(e.Location) == null) { arrastrando = true; arrastre = e.Location; }
    }

    protected override void OnMouseUp(MouseEventArgs e)
    {
        base.OnMouseUp(e);
        if (arrastrando) { arrastrando = false; return; }
        Zona z = ZonaEn(e.Location);
        if (e.Button == MouseButtons.Left && z != null) z.Click();
    }

    protected override void OnMouseWheel(MouseEventArgs e)
    {
        base.OnMouseWheel(e);
        scroll = Math.Max(0, scroll - e.Delta / 3);
    }

    Zona ZonaEn(Point p)
    {
        for (int i = zonas.Count - 1; i >= 0; i--) if (zonas[i].R.Contains(p)) return zonas[i];
        return null;
    }

    // ---------- dibujo ----------

    protected override void OnPaint(PaintEventArgs e)
    {
        Graphics g = e.Graphics;
        g.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;
        g.TextRenderingHint = System.Drawing.Text.TextRenderingHint.AntiAlias;
        zonas.Clear();

        if (video != null) video.Dibujar(g, tiempo.Elapsed.TotalSeconds);
        Sombra(g, new Rectangle(0, 0, Ancho, 140), 200, 0, 90f);
        Sombra(g, new Rectangle(0, Alto - 300, 760, 300), 0, 235, 90f);
        Sombra(g, new Rectangle(0, 0, 520, Alto), 150, 0, 0f);

        DibujarArriba(g);
        if (pestana == "noticias") DibujarNoticias(g);
        else if (pestana == "mods") DibujarMods(g);
        else if (pestana == "juego") DibujarJuego(g);
        else DibujarInicio(g);
        DibujarTarjeta(g);
        DibujarPie(g);
    }

    void DibujarArriba(Graphics g)
    {
        Estrella(g, 52, 38, 17, Acento);
        Neon(g, "America RP", Fuentes.Titulo(34f), 76, 20);

        int x = 300;
        foreach (string[] p in new[] { new[] { "inicio", "INICIO" }, new[] { "noticias", "NOTICIAS" }, new[] { "mods", "MODS" }, new[] { "juego", "MI JUEGO" } })
        {
            Font f = Fuentes.Titulo(19f);
            int w = Medir(g, p[1], f);
            var r = new Rectangle(x - 8, 20, w + 16, 40);
            bool activa = pestana == p[0], sobre = r.Contains(mouse);
            Escribir(g, p[1], f, activa || sobre ? Texto : Gris, x, 26);
            if (activa) using (var b = new SolidBrush(Acento)) g.FillRectangle(b, x, 56, 22, 3);
            string cap = p[0];
            zonas.Add(new Zona { R = r, Click = delegate { Pestana(cap); } });
            x += w + 30;
        }

        Linea(g, new Rectangle(Ancho - 56, 22, 36, 36), true, delegate { Close(); });
        Linea(g, new Rectangle(Ancho - 96, 22, 36, 36), false, delegate { WindowState = FormWindowState.Minimized; });
    }

    void DibujarInicio(Graphics g)
    {
        int y = Contenido.Bottom - 150;
        Escribir(g, "SERVIDOR DE ROLEPLAY EN ESPAÑOL", Fuentes.Negrita(10f), Acento, 44, y);
        Escribir(g, "BIENVENIDO A AMERICA RP", Fuentes.Titulo(58f), Texto, 40, y + 18);
        string primera = noticias.Replace("\r", "").Split('\n').FirstOrDefault(l => l.Trim().Length > 0 && !l.Contains("Bienvenido")) ?? "";
        using (var b = new SolidBrush(Color.FromArgb(220, Texto)))
            g.DrawString(primera, Fuentes.Texto(13f), b, new RectangleF(44, y + 104, 600, 50));
    }

    Rectangle Hoja(Graphics g, string titulo)
    {
        Vidrio(g, Contenido);
        Escribir(g, titulo, Fuentes.Titulo(34f), Texto, Contenido.X + 28, Contenido.Y + 20);
        return new Rectangle(Contenido.X + 28, Contenido.Y + 76, Contenido.Width - 56, Contenido.Height - 96);
    }

    void DibujarNoticias(Graphics g)
    {
        Rectangle area = Hoja(g, "NOTICIAS");
        Font f = Fuentes.Texto(13f);
        using (var b = new SolidBrush(Texto))
        {
            int alto = (int)g.MeasureString(noticias, f, area.Width).Height;
            scroll = Math.Min(scroll, Math.Max(0, alto - area.Height));
            g.SetClip(area);
            g.DrawString(noticias, f, b, new RectangleF(area.X, area.Y - scroll, area.Width, alto + 20));
            g.ResetClip();
        }
    }

    void DibujarMods(Graphics g)
    {
        Rectangle area = Hoja(g, "MODS DEL SERVER");
        if (revision == null || revision.Entradas.Count == 0)
        {
            Escribir(g, mods.Length == 0 ? "Revisando..." : mods, Fuentes.Texto(13f), Gris, area.X, area.Y);
            return;
        }
        int pend = revision.Pendientes.Count;
        Escribir(g, revision.Entradas.Count + " archivo(s) · " + (pend == 0 ? "todo al día" : pend + " por bajar"), Fuentes.Texto(12f), Gris, area.X, area.Y);
        if (pend > 0) Boton(g, new Rectangle(Contenido.Right - 180, Contenido.Y + 28, 150, 36), "BAJAR AHORA", true, Actualizar);
        var lista = new Rectangle(area.X - 10, area.Y + 32, area.Width + 20, area.Height - 32);
        scroll = Math.Min(scroll, Math.Max(0, revision.Entradas.Count * 36 - lista.Height));
        g.SetClip(lista);
        for (int i = 0; i < revision.Entradas.Count; i++)
        {
            int fy = lista.Y + i * 36 - scroll;
            if (fy + 36 < lista.Y || fy > lista.Bottom) continue;
            string ruta = revision.Entradas[i].Value;
            bool falta = revision.Pendientes.Contains(ruta);
            using (var p = new Pen(Color.FromArgb(28, 255, 255, 255))) g.DrawLine(p, lista.X, fy + 35, lista.Right, fy + 35);
            Escribir(g, Recortar(g, ruta, lista.Width - 150, Fuentes.Texto(12.5f)), Fuentes.Texto(12.5f), Texto, lista.X + 10, fy + 8);
            string t = falta ? "POR BAJAR" : "INSTALADO";
            Escribir(g, t, Fuentes.Titulo(16f), falta ? Ambar : Verde, lista.Right - 10 - Medir(g, t, Fuentes.Titulo(16f)), fy + 8);
        }
        g.ResetClip();
    }

    void DibujarJuego(Graphics g)
    {
        Rectangle area = Hoja(g, "MI JUEGO");
        string carpeta = Carpeta();
        Escribir(g, "CARPETA DEL GTA SAN ANDREAS", Fuentes.Negrita(10f), Gris, area.X, area.Y);
        Escribir(g, carpeta.Length == 0 ? "Sin elegir" : Recortar(g, carpeta, area.Width - 200, Fuentes.Texto(13f)), Fuentes.Texto(13f), Texto, area.X, area.Y + 20);
        Boton(g, new Rectangle(area.Right - 170, area.Y + 6, 170, 38), "CAMBIAR CARPETA", false, delegate { ElegirCarpeta(); });

        int y = area.Y + 80;
        foreach (string[] fila in Revisiones())
        {
            Color c = fila[2] == "ok" ? Verde : fila[2] == "mal" ? Rojo : fila[2] == "ojo" ? Ambar : Gris;
            using (var p = new Pen(Color.FromArgb(28, 255, 255, 255))) g.DrawLine(p, area.X, y + 44, area.Right, y + 44);
            Escribir(g, fila[0], Fuentes.Negrita(13f), Texto, area.X, y + 10);
            Escribir(g, fila[1], Fuentes.Titulo(18f), c, area.Right - Medir(g, fila[1], Fuentes.Titulo(18f)), y + 9);
            y += 46;
        }
        if (Config.EnbUrl.Length > 0)
        {
            bool activo = EnbActivo();
            Escribir(g, "GTA FULL · GRÁFICOS ENB", Fuentes.Negrita(13f), Texto, area.X, y + 10);
            Escribir(g, activo ? "ACTIVADO" : "DESACTIVADO", Fuentes.Titulo(18f), activo ? Verde : Gris, area.Right - 300, y + 9);
            Boton(g, new Rectangle(area.Right - 150, y + 4, 150, 34), activo ? "DESACTIVAR" : "ACTIVAR", false, CambiarEnb);
            Escribir(g, "Luces y colores mejorados. Pide más PC: si el juego anda lento, desactivalo.", Fuentes.Texto(11f), Gris, area.X, y + 40);
            y += 66;
        }
        Boton(g, new Rectangle(area.X, y + 24, 200, 40), "REVISAR Y ACTUALIZAR", true, Actualizar);
    }

    // [nombre, valor, ok|ojo|mal|nada]
    List<string[]> Revisiones()
    {
        string carpeta = Carpeta();
        bool hayGta = carpeta.Length > 0 && File.Exists(Path.Combine(carpeta, "gta_sa.exe"));
        bool haySamp = hayGta && faltantes.Count == 0;
        int pend = revision == null ? -1 : revision.Pendientes.Count;
        return new List<string[]>
        {
            new[] { "GTA San Andreas 1.0", !hayGta ? "FALTA" : gta10 ? "OK" : "REVISAR", !hayGta ? "mal" : gta10 ? "ok" : "ojo" },
            new[] { "SA-MP 0.3.7", haySamp ? "OK" : "FALTA", haySamp ? "ok" : "mal" },
            new[] { "Archivos del server", pend < 0 ? "-" : pend == 0 ? "AL DÍA" : pend + " POR BAJAR", pend < 0 ? "nada" : pend == 0 ? "ok" : "ojo" },
        };
    }

    void DibujarTarjeta(Graphics g)
    {
        Rectangle t = Tarjeta;
        Vidrio(g, t);
        using (var b = new SolidBrush(Acento)) g.FillRectangle(b, t.X, t.Y, t.Width, 3);
        int x = t.X + 28;

        Escribir(g, "SERVIDOR", Fuentes.Negrita(9.5f), Gris, x, t.Y + 24);
        Escribir(g, Recortar(g, server.EnLinea && server.Nombre.Length > 0 ? server.Nombre.ToUpperInvariant() : "AMERICA RP", t.Width - 56, Fuentes.Titulo(28f)), Fuentes.Titulo(28f), Texto, x, t.Y + 40);
        Color c = !serverConsultado ? Gris : server.EnLinea ? Verde : Rojo;
        Punto(g, x + 4, t.Y + 88, c);
        Escribir(g, !serverConsultado ? "CONSULTANDO..." : server.EnLinea ? "EN LÍNEA · " + server.Ping + " MS" : "APAGADO", Fuentes.Negrita(10f), c, x + 14, t.Y + 79);

        string num = server.EnLinea ? server.Jugadores.ToString() : "0";
        Escribir(g, num, Fuentes.Titulo(80f), Texto, x - 4, t.Y + 100);
        int nx = x + Medir(g, num, Fuentes.Titulo(80f)) + 4;
        Escribir(g, "/ " + (server.EnLinea ? server.Maximo : 0), Fuentes.Titulo(26f), Gris, nx, t.Y + 132);
        Escribir(g, "JUGADORES", Fuentes.Negrita(9.5f), Gris, nx + 2, t.Y + 164);

        using (var p = new Pen(Color.FromArgb(36, 255, 255, 255))) g.DrawLine(p, x, t.Y + 212, t.Right - 28, t.Y + 212);
        Escribir(g, "TU NICK", Fuentes.Negrita(9.5f), Gris, x, t.Y + 228);
        var caja = new Rectangle(x, t.Y + 250, t.Width - 56, 48);
        using (var b = new SolidBrush(Color.FromArgb(20, 22, 30))) g.FillRectangle(b, caja);
        using (var p = new Pen(nick.Focused ? Acento : Color.FromArgb(60, 255, 255, 255))) g.DrawRectangle(p, caja);

        int y = t.Y + 318;
        foreach (string[] fila in Revisiones())
        {
            Color fc = fila[2] == "ok" ? Verde : fila[2] == "mal" ? Rojo : fila[2] == "ojo" ? Ambar : Gris;
            Punto(g, x + 4, y + 10, fc);
            Escribir(g, fila[0], Fuentes.Texto(11f), Texto, x + 16, y + 1);
            Escribir(g, fila[1], Fuentes.Titulo(15f), fc, t.Right - 28 - Medir(g, fila[1], Fuentes.Titulo(15f)), y);
            y += 26;
        }

        // Botón inclinado: el borde en diagonal le da otro aire que un rectángulo redondeado.
        var jugar = new Rectangle(x, t.Bottom - 96, t.Width - 56, 68);
        bool sobre = jugar.Contains(mouse) && !ocupado;
        var forma = new[] { new Point(jugar.X + 14, jugar.Y), new Point(jugar.Right, jugar.Y), new Point(jugar.Right - 14, jugar.Bottom), new Point(jugar.X, jugar.Bottom) };
        using (var b = new SolidBrush(ocupado ? Color.FromArgb(120, Acento) : sobre ? Color.FromArgb(255, 186, 72) : Acento)) g.FillPolygon(b, forma);
        string txt = ocupado ? "ESPERÁ..." : "JUGAR";
        Escribir(g, txt, Fuentes.Titulo(40f), Oscuro, jugar.X + (jugar.Width - Medir(g, txt, Fuentes.Titulo(40f))) / 2, jugar.Y + 10);
        if (!ocupado) zonas.Add(new Zona { R = jugar, Click = Jugar });
    }

    void DibujarPie(Graphics g)
    {
        using (var b = new SolidBrush(Color.FromArgb(40, 255, 255, 255))) g.FillRectangle(b, 0, Alto - 3, Ancho, 3);
        if (progreso > 0) using (var b = new SolidBrush(Acento)) g.FillRectangle(b, 0, Alto - 3, Ancho * progreso / 100, 3);
        Escribir(g, Recortar(g, (ocupado ? "● " : "") + estado, 640, Fuentes.Texto(11f)), Fuentes.Texto(11f), Gris, 40, Alto - 36);

        int x = Tarjeta.Right;
        for (int i = Config.Redes.Length - 1; i >= 0; i--)
        {
            if (Config.Redes[i].Value.Length == 0) continue;
            string t = Config.Redes[i].Key.ToUpperInvariant(), url = Config.Redes[i].Value;
            int w = Medir(g, t, Fuentes.Titulo(17f));
            x -= w;
            var r = new Rectangle(x - 4, Alto - 40, w + 8, 30);
            Escribir(g, t, Fuentes.Titulo(17f), r.Contains(mouse) ? Acento : Gris, x, Alto - 37);
            zonas.Add(new Zona { R = r, Click = delegate { Abrir(url); } });
            x -= 22;
        }
    }

    // ---------- piezas ----------

    void Boton(Graphics g, Rectangle r, string texto, bool principal, Action click)
    {
        bool sobre = r.Contains(mouse);
        if (principal) using (var b = new SolidBrush(sobre ? Color.FromArgb(255, 186, 72) : Acento)) g.FillRectangle(b, r);
        else using (var p = new Pen(sobre ? Acento : Color.FromArgb(120, 255, 255, 255), 1.5f)) g.DrawRectangle(p, r);
        Font f = Fuentes.Titulo(18f);
        Escribir(g, texto, f, principal ? Oscuro : Texto, r.X + (r.Width - Medir(g, texto, f)) / 2, r.Y + (r.Height - 26) / 2);
        zonas.Add(new Zona { R = r, Click = click });
    }

    void Linea(Graphics g, Rectangle r, bool cruz, Action click)
    {
        bool sobre = r.Contains(mouse);
        if (sobre) using (var b = new SolidBrush(Color.FromArgb(cruz ? 200 : 60, cruz ? Rojo : Color.White))) g.FillRectangle(b, r);
        using (var p = new Pen(Texto, 1.6f))
        {
            int cx = r.X + r.Width / 2, cy = r.Y + r.Height / 2;
            if (cruz) { g.DrawLine(p, cx - 6, cy - 6, cx + 6, cy + 6); g.DrawLine(p, cx + 6, cy - 6, cx - 6, cy + 6); }
            else g.DrawLine(p, cx - 7, cy, cx + 7, cy);
        }
        zonas.Add(new Zona { R = r, Click = click });
    }

    static void Vidrio(Graphics g, Rectangle r)
    {
        using (var b = new SolidBrush(Color.FromArgb(205, 10, 12, 18))) g.FillRectangle(b, r);
        using (var p = new Pen(Color.FromArgb(34, 255, 255, 255))) g.DrawRectangle(p, r);
    }

    static void Sombra(Graphics g, Rectangle r, int desde, int hasta, float angulo)
    {
        // El pincel es 2 px más grande: si no, en el borde repite el color del otro extremo y se ve una raya.
        var mayor = Rectangle.Inflate(r, 2, 2);
        using (var b = new System.Drawing.Drawing2D.LinearGradientBrush(mayor, Color.FromArgb(desde, Oscuro), Color.FromArgb(hasta, Oscuro), angulo))
            g.FillRectangle(b, r);
    }

    // Letras con brillo azul, como el logo del video.
    static void Neon(Graphics g, string texto, Font f, int x, int y)
    {
        using (var camino = new System.Drawing.Drawing2D.GraphicsPath())
        {
            camino.AddString(texto, f.FontFamily, (int)f.Style, g.DpiY * f.SizeInPoints / 72f, new Point(x, y), StringFormat.GenericTypographic);
            foreach (int ancho in new[] { 10, 6, 3 })
                using (var p = new Pen(Color.FromArgb(ancho == 10 ? 40 : ancho == 6 ? 80 : 200, 60, 150, 255), ancho)) { p.LineJoin = System.Drawing.Drawing2D.LineJoin.Round; g.DrawPath(p, camino); }
            using (var b = new SolidBrush(Color.White)) g.FillPath(b, camino);
        }
    }

    static void Punto(Graphics g, int x, int y, Color c)
    {
        using (var b = new SolidBrush(c)) g.FillEllipse(b, x - 4, y - 4, 8, 8);
    }

    static void Estrella(Graphics g, int cx, int cy, int radio, Color c)
    {
        var pts = new PointF[10];
        for (int i = 0; i < 10; i++)
        {
            double ang = -Math.PI / 2 + i * Math.PI / 5;
            float r = i % 2 == 0 ? radio : radio * 0.42f;
            pts[i] = new PointF(cx + (float)(Math.Cos(ang) * r), cy + (float)(Math.Sin(ang) * r));
        }
        using (var b = new SolidBrush(c)) g.FillPolygon(b, pts);
    }

    static void Escribir(Graphics g, string texto, Font f, Color c, int x, int y)
    {
        using (var b = new SolidBrush(c)) g.DrawString(texto, f, b, x, y);
    }

    static int Medir(Graphics g, string texto, Font f)
    {
        return (int)g.MeasureString(texto, f, PointF.Empty, StringFormat.GenericTypographic).Width;
    }

    static string Recortar(Graphics g, string texto, int ancho, Font f)
    {
        if (Medir(g, texto, f) <= ancho) return texto;
        while (texto.Length > 1 && Medir(g, "..." + texto, f) > ancho) texto = texto.Substring(1);
        return "..." + texto;
    }
}

static class Web
{
    public static string Texto(string url)
    {
        using (var web = new WebClient()) { web.Encoding = Encoding.UTF8; return web.DownloadString(url); }
    }
}

// Fondo en video: fondo/video.bin va dentro del .exe (lo arma fondo/armar_video.py) y se repite en bucle.
// Son JPEG ya del tamaño de la ventana; se descomprime solo el cuadro que toca, así no ocupa cientos de MB.
class Video
{
    readonly byte[] datos;
    readonly List<int> inicios = new List<int>(), largos = new List<int>();
    readonly int fps;
    int actual = -1;
    Image cuadro;

    Video(byte[] datos)
    {
        this.datos = datos;
        if (datos.Length < 16 || Encoding.ASCII.GetString(datos, 0, 8) != "AMRPVID1") throw new InvalidDataException("video.bin inválido");
        fps = Math.Max(1, BitConverter.ToInt32(datos, 8));
        int n = BitConverter.ToInt32(datos, 12), pos = 16;
        for (int i = 0; i < n && pos + 4 <= datos.Length; i++)
        {
            int largo = BitConverter.ToInt32(datos, pos);
            if (largo <= 0 || pos + 4 + largo > datos.Length) break;
            inicios.Add(pos + 4);
            largos.Add(largo);
            pos += 4 + largo;
        }
        if (inicios.Count == 0) throw new InvalidDataException("video.bin sin cuadros");
    }

    public int Cuadros { get { return inicios.Count; } }

    public static Video Desde(byte[] datos) { return new Video(datos); }

    // Sin video (compilado sin el recurso o roto) el fondo queda liso.
    public static Video Cargar()
    {
        try
        {
            using (Stream s = typeof(Video).Assembly.GetManifestResourceStream("video.bin"))
            {
                if (s == null) return null;
                var ms = new MemoryStream();
                s.CopyTo(ms);
                return new Video(ms.ToArray());
            }
        }
        catch (Exception) { return null; }
    }

    public void Dibujar(Graphics g, double t)
    {
        int i = (int)(t * fps) % inicios.Count;
        if (i != actual)
        {
            try
            {
                Image nuevo;
                using (var ms = new MemoryStream(datos, inicios[i], largos[i])) using (Image img = Image.FromStream(ms)) nuevo = new Bitmap(img);
                if (cuadro != null) cuadro.Dispose();
                cuadro = nuevo;
            }
            catch (Exception) { }
            actual = i;
        }
        if (cuadro == null) return;
        g.InterpolationMode = System.Drawing.Drawing2D.InterpolationMode.Bilinear;
        g.DrawImage(cuadro, 0, 0, 1100, 660);
    }
}

static class Programa
{
    [STAThread]
    static int Main(string[] args)
    {
        // Windows 7/8 no usan TLS 1.2 por defecto y GitHub lo exige.
        ServicePointManager.SecurityProtocol |= (SecurityProtocolType)3072;
        if (args.Length == 1 && args[0] == "--prueba") return Prueba.Correr();
        if (args.Length == 2 && args[0] == "--manifiesto")
        {
            string salida = Path.Combine(Path.GetDirectoryName(Path.GetFullPath(args[1]).TrimEnd(Path.DirectorySeparatorChar)), Actualizador.NombreManifiesto);
            File.WriteAllText(salida, Actualizador.GenerarManifiesto(args[1]), new UTF8Encoding(false));
            Console.WriteLine("Manifiesto escrito en " + salida);
            return 0;
        }
        Application.EnableVisualStyles();
        Application.Run(new Ventana());
        return 0;
    }
}

// AmericaRP.exe --prueba: revisa la lógica que no necesita ventana (corre también con mono en Linux).
static class Prueba
{
    static int fallas;

    static void Ver(bool ok, string que)
    {
        Console.WriteLine((ok ? "OK    " : "FALLA ") + que);
        if (!ok) fallas++;
    }

    static string Sha(Stream s)
    {
        using (var sha = SHA256.Create()) return BitConverter.ToString(sha.ComputeHash(s)).Replace("-", "").ToLowerInvariant();
    }

    static bool Tira(Action a)
    {
        try { a(); return false; } catch (InvalidDataException) { return true; }
    }

    public static int Correr()
    {
        byte[] pedido = Consulta.ArmarPedido(IPAddress.Parse("1.2.3.4"), 7777, (byte)'i');
        Ver(Encoding.ASCII.GetString(pedido, 0, 4) == "SAMP" && pedido[4] == 1 && pedido[7] == 4 && pedido[8] == 0x61 && pedido[9] == 0x1E && pedido[10] == 'i', "pedido de consulta");

        var r = new List<byte>(pedido) { 0 };
        r.AddRange(BitConverter.GetBytes((ushort)12));
        r.AddRange(BitConverter.GetBytes((ushort)100));
        byte[] nombre = Consulta.Texto1252().GetBytes("AMERICA RP Español");
        r.AddRange(BitConverter.GetBytes(nombre.Length));
        r.AddRange(nombre);
        EstadoServidor e = Consulta.Leer(r.ToArray());
        Ver(e.EnLinea && e.Jugadores == 12 && e.Maximo == 100 && e.Nombre == "AMERICA RP Español", "respuesta de consulta");
        Ver(!Consulta.Leer(new byte[] { 1, 2, 3 }).EnLinea, "respuesta corta se ignora");
        r[18] = 0xFF; // largo del nombre absurdo
        Ver(Consulta.Leer(r.ToArray()).Nombre == "", "largo de nombre falso no rompe");

        string carpeta = Path.Combine(Path.GetTempPath(), "americarp-prueba-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(Path.Combine(carpeta, "archivos", "models"));
        try
        {
            Ver(Tira(() => Actualizador.RutaSegura(carpeta, "../fuera.txt")), "rechaza ..");
            Ver(Tira(() => Actualizador.RutaSegura(carpeta, "C:/Windows/x.dll")), "rechaza ruta con unidad");
            Ver(Tira(() => Actualizador.RutaSegura(carpeta, "/etc/x")), "rechaza ruta absoluta");
            Ver(Actualizador.RutaSegura(carpeta, "models/gta3.img").StartsWith(Path.GetFullPath(carpeta)), "acepta ruta interna");
            Ver(Actualizador.UrlArchivo("https://x.com/a/actualizaciones/manifiesto.txt", "models/mi mod.txd") == "https://x.com/a/actualizaciones/archivos/models/mi%20mod.txd", "url del archivo");

            File.WriteAllText(Path.Combine(carpeta, "archivos", "models", "a.txt"), "abc");
            string m = Actualizador.GenerarManifiesto(Path.Combine(carpeta, "archivos"));
            var entradas = Actualizador.LeerManifiesto(m);
            Ver(entradas.Count == 1 && entradas[0].Key == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad" && entradas[0].Value == "models/a.txt", "manifiesto generado y leído");
            Ver(Tira(() => Actualizador.LeerManifiesto("hola mundo")), "manifiesto inválido se rechaza");

            // Quitar: borra lo instalado, pero no un archivo que el jugador cambió.
            string gta = Path.Combine(carpeta, "gta");
            Directory.CreateDirectory(Path.Combine(gta, "models"));
            File.WriteAllText(Path.Combine(gta, "models", "a.txt"), "abc");
            File.WriteAllText(Path.Combine(gta, "d3d9.dll"), "mio");
            string m2 = m + "0000000000000000000000000000000000000000000000000000000000000000 d3d9.dll\n";
            Ver(Actualizador.Quitar(gta, m2) == 1 && !File.Exists(Path.Combine(gta, "models", "a.txt")) && File.Exists(Path.Combine(gta, "d3d9.dll")), "quitar paquete respeta archivos propios");
            Ver(Tira(() => Actualizador.Quitar(gta, "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad ../afuera.txt")), "quitar rechaza rutas de afuera");

            // Zip del ENB: versión equivocada, archivo de otro mod y la instalación buena.
            string zip = Path.Combine(carpeta, "enb.zip");
            using (ZipArchive z = ZipFile.Open(zip, ZipArchiveMode.Create))
            {
                foreach (string[] f in new[] { new[] { "WrapperVersion/d3d9.dll", "dll" }, new[] { "WrapperVersion/enbseries/enbhelper.dll", "h" }, new[] { "AsiVersion/enbseries.asi", "asi" } })
                    using (var w = new StreamWriter(z.CreateEntry(f[0]).Open())) w.Write(f[1]);
            }
            string shaAsi;
            using (var ms = new MemoryStream(Encoding.ASCII.GetBytes("asi"))) shaAsi = Sha(ms);
            Ver(Tira(() => Actualizador.InstalarZipEnb(gta, zip, "otro")), "zip ENB: rechaza otra versión");
            File.WriteAllText(Path.Combine(gta, "enbseries.asi"), "de otro");
            Ver(Tira(() => Actualizador.InstalarZipEnb(gta, zip, shaAsi)) && !File.Exists(Path.Combine(gta, "enbseries", "enbhelper.dll")), "zip ENB: no pisa archivos de otro mod ni copia nada");
            File.Delete(Path.Combine(gta, "enbseries.asi"));
            File.WriteAllText(Path.Combine(gta, "dinput8.dll"), "otro loader");
            Ver(Tira(() => Actualizador.InstalarZipEnb(gta, zip, shaAsi)), "zip ENB: no pisa el dinput8.dll de otro mod");
            File.Delete(Path.Combine(gta, "dinput8.dll"));
            List<string> inst = Actualizador.InstalarZipEnb(gta, zip, shaAsi);
            Ver(inst.Count == 2 && File.ReadAllText(Path.Combine(gta, "enbseries.asi")) == "asi" && File.ReadAllText(Path.Combine(gta, "d3d9.dll")) == "mio", "zip ENB: instala el .asi y deja afuera su d3d9.dll");
            Ver(Actualizador.Quitar(gta, Actualizador.Huellas(gta, inst)) == 2 && !File.Exists(Path.Combine(gta, "enbseries.asi")) && File.Exists(Path.Combine(gta, "d3d9.dll")), "zip ENB: se saca entero");
        }
        finally { Directory.Delete(carpeta, true); }

        var vid = new List<byte>(Encoding.ASCII.GetBytes("AMRPVID1"));
        vid.AddRange(BitConverter.GetBytes(24));
        vid.AddRange(BitConverter.GetBytes(5)); // dice 5 cuadros pero trae 2 y uno cortado
        for (int i = 0; i < 2; i++) { vid.AddRange(BitConverter.GetBytes(3)); vid.AddRange(new byte[] { 1, 2, 3 }); }
        vid.AddRange(BitConverter.GetBytes(999));
        Ver(Video.Desde(vid.ToArray()).Cuadros == 2, "video: lee solo los cuadros completos");
        Ver(Tira(() => Video.Desde(Encoding.ASCII.GetBytes("cualquier cosa nada"))), "video: rechaza archivo que no es video");

        Ver(Instalacion.NickValido.IsMatch("Juan_Perez") && !Instalacion.NickValido.IsMatch("ab") && !Instalacion.NickValido.IsMatch("con espacio"), "nick");
        Console.WriteLine(fallas == 0 ? "Todo bien." : fallas + " falla(s).");
        return fallas == 0 ? 0 : 1;
    }
}
