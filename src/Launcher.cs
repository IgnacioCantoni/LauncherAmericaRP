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
    public const string DescargaSampUrl = "https://www.sa-mp.mp/downloads/";
    // Imagen de fondo (JPG o PNG, ideal 1100x640). Si no está en el repo, se usa un fondo dibujado.
    public const string FondoUrl = Repo + "fondo.jpg";
    // Botón "Soporte" arriba a la derecha. Vacío = no aparece.
    public const string Soporte = "";
    // Botones de redes en el lateral, en este orden. Los que tengan el link vacío no aparecen.
    public static readonly KeyValuePair<string, string>[] Redes =
    {
        new KeyValuePair<string, string>("Discord", ""),
        new KeyValuePair<string, string>("YouTube", ""),
        new KeyValuePair<string, string>("TikTok", ""),
        new KeyValuePair<string, string>("Instagram", ""),
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
    }

    // Baja el manifiesto y marca qué archivos el jugador no tiene o tiene distintos.
    public static Revision Revisar(string carpetaGta, string manifiestoUrl, Action<string, int> progreso)
    {
        var r = new Revision();
        progreso("Buscando actualizaciones...", 0);
        using (var web = new WebClient())
        {
            web.Encoding = Encoding.UTF8;
            r.Entradas = LeerManifiesto(web.DownloadString(manifiestoUrl));
        }
        for (int i = 0; i < r.Entradas.Count; i++)
        {
            string destino = RutaSegura(carpetaGta, r.Entradas[i].Value);
            progreso("Revisando " + r.Entradas[i].Value, 100 * i / Math.Max(1, r.Entradas.Count));
            if (!File.Exists(destino) || Sha256(destino) != r.Entradas[i].Key) r.Pendientes.Add(r.Entradas[i].Value);
        }
        return r;
    }

    // Devuelve cuántos archivos bajó. Si algo falla, tira la excepción y no deja archivos a medias.
    public static int Aplicar(string carpetaGta, string manifiestoUrl, Action<string, int> progreso)
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
        return pendientes.Count;
    }
}

// La ventana se dibuja entera a mano (sin bordes de Windows) para poder poner el fondo y los paneles translúcidos.
// Los botones son zonas: cada vez que se pinta se anotan su rectángulo y su acción.
class Ventana : Form
{
    static readonly Color Acento = Color.FromArgb(242, 157, 56), Acento2 = Color.FromArgb(224, 83, 47),
        Texto = Color.FromArgb(240, 242, 247), Gris = Color.FromArgb(160, 166, 182), Oscuro = Color.FromArgb(12, 14, 20),
        Verde = Color.FromArgb(88, 214, 130), Rojo = Color.FromArgb(235, 92, 92), Ambar = Color.FromArgb(245, 196, 80);
    const int Ancho = 1100, Alto = 640, Barra = 76;

    class Zona { public Rectangle R; public Action Click; }
    readonly List<Zona> zonas = new List<Zona>();
    readonly TextBox nick = new TextBox();
    readonly Timer reloj = new Timer();
    Point mouse = new Point(-1, -1), arrastre;
    bool arrastrando, consultando, ocupado;

    Image fondo;
    EstadoServidor server = new EstadoServidor();
    bool serverConsultado;
    string pestana = "inicio", noticias = "Cargando noticias...", estado = "Listo.", mods = "";
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
        nick.BackColor = Color.FromArgb(24, 27, 36);
        nick.ForeColor = Texto;
        nick.Font = new Font("Segoe UI", 12f, FontStyle.Bold);
        nick.MaxLength = 20;
        nick.SetBounds(78, Alto - Barra + 26, 196, 24);
        nick.Text = Registro.Nick;
        nick.TextChanged += delegate { Invalidate(); };
        Controls.Add(nick);

        fondo = Fondo.Cargado() ?? Fondo.Generado(Ancho, Alto);
        RevisarInstalacion();
        reloj.Interval = 15000;
        reloj.Tick += delegate { RefrescarServer(); };
        Shown += delegate
        {
            ActiveControl = nick;
            nick.SelectionStart = nick.Text.Length;
            reloj.Start();
            RefrescarServer();
            CargarNoticias();
            CargarFondo();
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
        Invalidate();
    }

    void Avisar(string texto, int porcentaje)
    {
        if (InvokeRequired) { BeginInvoke(new Action<string, int>(Avisar), texto, porcentaje); return; }
        estado = texto;
        progreso = Math.Max(0, Math.Min(100, porcentaje));
        Invalidate();
    }

    async void RefrescarServer()
    {
        if (consultando) return;
        consultando = true;
        server = await Task.Run(() => Consulta.Pedir(Config.Host, Config.Puerto, 2500));
        serverConsultado = true;
        consultando = false;
        Invalidate();
    }

    async void CargarNoticias()
    {
        if (Config.NoticiasUrl.Length == 0) { noticias = "Todavía no hay noticias."; return; }
        try { noticias = await Task.Run(() => Web.Texto(Config.NoticiasUrl)); }
        catch (Exception ex) { noticias = "No se pudieron cargar las noticias: " + ex.Message; }
        Invalidate();
    }

    async void CargarFondo()
    {
        Image nuevo = await Task.Run(() => Fondo.Bajar());
        if (nuevo != null) { fondo = nuevo; Invalidate(); }
    }

    async void RevisarMods()
    {
        if (Config.ManifiestoUrl.Length == 0) { mods = "Este server no reparte archivos propios."; return; }
        if (faltantes.Count > 0 && Carpeta().Length == 0) { mods = "Elegí la carpeta del GTA para ver tus archivos."; Invalidate(); return; }
        string carpeta = Carpeta();
        try
        {
            revision = await Task.Run(() => Actualizador.Revisar(carpeta, Config.ManifiestoUrl, delegate { }));
            mods = revision.Entradas.Count == 0 ? "Todavía no hay mods ni archivos del server." : "";
        }
        catch (Exception ex) { revision = null; mods = "No se pudieron revisar los archivos: " + ex.Message; }
        Invalidate();
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
        Invalidate();
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
        pestana = pestana == p ? "inicio" : p;
        scroll = 0;
        Invalidate();
    }

    // ---------- mouse ----------

    protected override void OnMouseMove(MouseEventArgs e)
    {
        base.OnMouseMove(e);
        if (arrastrando) { Location = new Point(Location.X + e.X - arrastre.X, Location.Y + e.Y - arrastre.Y); return; }
        mouse = e.Location;
        Cursor = ZonaEn(e.Location) != null ? Cursors.Hand : Cursors.Default;
        Invalidate();
    }

    protected override void OnMouseLeave(EventArgs e)
    {
        base.OnMouseLeave(e);
        mouse = new Point(-1, -1);
        Invalidate();
    }

    protected override void OnMouseDown(MouseEventArgs e)
    {
        base.OnMouseDown(e);
        if (e.Button == MouseButtons.Left && e.Y < 70 && ZonaEn(e.Location) == null) { arrastrando = true; arrastre = e.Location; }
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
        Invalidate();
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
        g.TextRenderingHint = System.Drawing.Text.TextRenderingHint.AntiAliasGridFit;
        zonas.Clear();

        DibujarFondo(g);
        DibujarLateral(g);
        DibujarArriba(g);
        if (pestana == "noticias") DibujarNoticias(g);
        else if (pestana == "mods") DibujarMods(g);
        else DibujarInicio(g);
        DibujarBarra(g);
    }

    void DibujarFondo(Graphics g)
    {
        float esc = Math.Max((float)Ancho / fondo.Width, (float)Alto / fondo.Height);
        float w = fondo.Width * esc, h = fondo.Height * esc;
        g.DrawImage(fondo, (Ancho - w) / 2, (Alto - h) / 2, w, h);
        using (var b = new System.Drawing.Drawing2D.LinearGradientBrush(new Rectangle(0, 0, 520, Alto), Color.FromArgb(240, Oscuro), Color.FromArgb(0, Oscuro), 0f))
            g.FillRectangle(b, 0, 0, 520, Alto);
        using (var b = new System.Drawing.Drawing2D.LinearGradientBrush(new Rectangle(0, Alto - 260, Ancho, 260), Color.FromArgb(0, Oscuro), Color.FromArgb(230, Oscuro), 90f))
            g.FillRectangle(b, 0, Alto - 260, Ancho, 260);
    }

    void DibujarLateral(Graphics g)
    {
        // Logo propio: estrella y nombre.
        Estrella(g, 44, 46, 20, Acento);
        Escribir(g, "AMERICA", 74, 22, 21f, FontStyle.Bold, Texto);
        Escribir(g, "R O L E P L A Y", 77, 54, 8.5f, FontStyle.Bold, Acento);

        int x = 28;
        foreach (string p in new[] { "noticias", "mods" })
        {
            string t = p == "noticias" ? "NOTICIAS" : "MODS";
            int w = Medir(g, t, 9.5f, FontStyle.Bold) + 36;
            string cap = p;
            Pildora(g, new Rectangle(x, 96, w, 36), t, pestana == p, delegate { Pestana(cap); });
            x += w + 10;
        }

        Escribir(g, "Jugadores online", 30, 156, 11f, FontStyle.Regular, Gris);
        string num = server.EnLinea ? server.Jugadores.ToString() : "0";
        Escribir(g, num, 26, 176, 36f, FontStyle.Bold, Texto);
        if (server.EnLinea) Escribir(g, "/ " + server.Maximo, 34 + Medir(g, num, 36f, FontStyle.Bold), 198, 13f, FontStyle.Regular, Gris);
        string linea = !serverConsultado ? "Consultando el server..." : server.EnLinea ? "En línea · " + server.Ping + " ms" : "Server apagado o sin respuesta";
        Punto(g, 36, 241, !serverConsultado ? Gris : server.EnLinea ? Verde : Rojo);
        Escribir(g, linea, 46, 232, 10f, FontStyle.Regular, Gris);

        int y = 270;
        x = 28;
        foreach (KeyValuePair<string, string> red in Config.Redes)
        {
            if (red.Value.Length == 0) continue;
            int w = Medir(g, red.Key, 9.5f, FontStyle.Bold) + 30;
            string url = red.Value;
            Pildora(g, new Rectangle(x, y, w, 32), red.Key, false, delegate { Abrir(url); });
            x += w + 8;
        }

        y = 326;
        Escribir(g, "T U   J U E G O", 30, y, 8.5f, FontStyle.Bold, Gris);
        var tarjeta = new Rectangle(28, y + 24, 300, 172);
        Redondeado(g, tarjeta, 12, Color.FromArgb(200, 22, 25, 34), Color.FromArgb(60, 255, 255, 255));
        Escribir(g, "GTA San Andreas", 46, y + 38, 12.5f, FontStyle.Bold, Texto);
        string carpeta = Carpeta();
        Escribir(g, carpeta.Length == 0 ? "Carpeta sin elegir" : Recortar(g, carpeta, 260, 8.5f), 46, y + 62, 8.5f, FontStyle.Regular, Gris);

        bool hayGta = carpeta.Length > 0 && File.Exists(Path.Combine(carpeta, "gta_sa.exe"));
        bool haySamp = hayGta && faltantes.Count == 0;
        Estado(g, 46, y + 88, "Versión 1.0", !hayGta ? Rojo : gta10 ? Verde : Ambar, !hayGta ? "Falta" : gta10 ? "OK" : "Revisar");
        Estado(g, 46, y + 108, "SA-MP 0.3.7", haySamp ? Verde : Rojo, haySamp ? "OK" : "Falta");
        int pend = revision == null ? -1 : revision.Pendientes.Count;
        Estado(g, 46, y + 128, "Archivos del server", pend < 0 ? Gris : pend == 0 ? Verde : Ambar, pend < 0 ? "-" : pend == 0 ? "Al día" : pend + " por bajar");
        Pildora(g, new Rectangle(46, y + 156, 104, 28), "Cambiar", false, delegate { ElegirCarpeta(); });
    }

    void DibujarArriba(Graphics g)
    {
        int x = Ancho - 16;
        x -= 40; Icono(g, new Rectangle(x, 16, 40, 34), "✕", delegate { Close(); });
        x -= 46; Icono(g, new Rectangle(x, 16, 40, 34), "—", delegate { WindowState = FormWindowState.Minimized; });
        foreach (string t in Config.Soporte.Length > 0 ? new[] { "Actualizar", "Soporte" } : new[] { "Actualizar" })
        {
            int w = Medir(g, t, 9.5f, FontStyle.Bold) + 32;
            x -= w + 8;
            string cap = t;
            Pildora(g, new Rectangle(x, 16, w, 34), t, false, delegate { if (cap == "Soporte") Abrir(Config.Soporte); else Actualizar(); });
        }
        if (Instalacion.NickValido.IsMatch(nick.Text.Trim()))
        {
            int w = Medir(g, nick.Text.Trim(), 9.5f, FontStyle.Bold) + 46;
            x -= w + 8;
            var r = new Rectangle(x, 16, w, 34);
            Redondeado(g, r, 17, Color.FromArgb(170, 20, 60, 36), Color.FromArgb(160, Verde));
            Punto(g, x + 18, 33, Verde);
            Escribir(g, nick.Text.Trim(), x + 30, 23, 9.5f, FontStyle.Bold, Verde);
        }
    }

    void DibujarInicio(Graphics g)
    {
        Escribir(g, "Bienvenido a AMERICA RP", 380, Alto - Barra - 118, 26f, FontStyle.Bold, Texto);
        string primera = noticias.Replace("\r", "").Split('\n').FirstOrDefault(l => l.Trim().Length > 0 && !l.Contains("Bienvenido")) ?? "";
        using (var f = new Font("Segoe UI", 11f))
        using (var b = new SolidBrush(Gris))
            g.DrawString(primera, f, b, new RectangleF(383, Alto - Barra - 70, 640, 48));
    }

    Rectangle Panel(Graphics g, string titulo)
    {
        var r = new Rectangle(370, 74, Ancho - 370 - 24, Alto - Barra - 74 - 18);
        Redondeado(g, r, 14, Color.FromArgb(215, 16, 18, 26), Color.FromArgb(50, 255, 255, 255));
        Escribir(g, titulo, r.X + 26, r.Y + 20, 16f, FontStyle.Bold, Texto);
        Icono(g, new Rectangle(r.Right - 50, r.Y + 16, 34, 30), "✕", delegate { Pestana("inicio"); });
        return r;
    }

    void DibujarNoticias(Graphics g)
    {
        Rectangle r = Panel(g, "Noticias");
        var area = new Rectangle(r.X + 26, r.Y + 62, r.Width - 52, r.Height - 80);
        using (var f = new Font("Segoe UI", 11f))
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
        Rectangle r = Panel(g, "Mods y archivos del server");
        int y = r.Y + 62;
        if (revision == null || revision.Entradas.Count == 0)
        {
            Escribir(g, mods.Length == 0 ? "Revisando..." : mods, r.X + 26, y, 11f, FontStyle.Regular, Gris);
            return;
        }
        int pend = revision.Pendientes.Count;
        Escribir(g, revision.Entradas.Count + " archivo(s) · " + (pend == 0 ? "todo al día" : pend + " por bajar"), r.X + 26, y, 10f, FontStyle.Regular, Gris);
        if (pend > 0) Pildora(g, new Rectangle(r.Right - 200, r.Y + 16, 140, 30), "Bajar ahora", true, Actualizar);
        var area = new Rectangle(r.X + 16, y + 30, r.Width - 32, r.Bottom - y - 46);
        scroll = Math.Min(scroll, Math.Max(0, revision.Entradas.Count * 34 - area.Height));
        g.SetClip(area);
        for (int i = 0; i < revision.Entradas.Count; i++)
        {
            int fy = area.Y + i * 34 - scroll;
            if (fy + 34 < area.Y || fy > area.Bottom) continue;
            string ruta = revision.Entradas[i].Value;
            bool falta = revision.Pendientes.Contains(ruta);
            if (i % 2 == 0) using (var b = new SolidBrush(Color.FromArgb(18, 255, 255, 255))) g.FillRectangle(b, area.X, fy, area.Width, 34);
            Punto(g, area.X + 16, fy + 17, falta ? Ambar : Verde);
            Escribir(g, Recortar(g, ruta, area.Width - 160, 10f), area.X + 30, fy + 7, 10f, FontStyle.Regular, Texto);
            string t = falta ? "Por bajar" : "Instalado";
            Escribir(g, t, area.Right - 16 - Medir(g, t, 9.5f, FontStyle.Bold), fy + 8, 9.5f, FontStyle.Bold, falta ? Ambar : Verde);
        }
        g.ResetClip();
    }

    void DibujarBarra(Graphics g)
    {
        int y = Alto - Barra;
        using (var b = new SolidBrush(Color.FromArgb(250, 10, 11, 16))) g.FillRectangle(b, 0, y, Ancho, Barra);
        using (var p = new Pen(Color.FromArgb(40, 255, 255, 255))) g.DrawLine(p, 0, y, Ancho, y);

        Redondeado(g, new Rectangle(24, y + 14, 266, 48), 10, Color.FromArgb(24, 27, 36), Color.FromArgb(50, 255, 255, 255));
        using (var b = new SolidBrush(Gris))
        {
            g.FillEllipse(b, 44, y + 26, 12, 12);
            g.FillPie(b, 38, y + 40, 24, 22, 180, 180);
        }

        int px = 316, pw = 420;
        Escribir(g, ocupado ? "T R A B A J A N D O" : "E S T A D O", px, y + 14, 8.5f, FontStyle.Bold, Gris);
        Redondeado(g, new Rectangle(px, y + 36, pw, 6), 3, Color.FromArgb(40, 255, 255, 255), Color.Empty);
        if (progreso > 0)
            using (var b = new System.Drawing.Drawing2D.LinearGradientBrush(new Rectangle(px, y + 36, pw, 6), Acento, Acento2, 0f))
                g.FillRectangle(b, px, y + 36, pw * progreso / 100, 6);
        Escribir(g, Recortar(g, estado, pw, 9f), px, y + 46, 9f, FontStyle.Regular, Gris);

        var srv = new Rectangle(758, y + 14, 150, 48);
        Redondeado(g, srv, 10, Color.FromArgb(24, 27, 36), Color.FromArgb(50, 255, 255, 255));
        Punto(g, srv.X + 18, srv.Y + 24, server.EnLinea ? Verde : Rojo);
        Escribir(g, Recortar(g, server.EnLinea && server.Nombre.Length > 0 ? server.Nombre : "AMERICA RP", 110, 10f), srv.X + 30, srv.Y + 5, 10f, FontStyle.Bold, Texto);
        Escribir(g, server.EnLinea ? server.Jugadores + " jugadores" : "Apagado", srv.X + 30, srv.Y + 25, 8.5f, FontStyle.Regular, Gris);

        var jugar = new Rectangle(922, y + 12, 154, 52);
        bool sobre = jugar.Contains(mouse) && !ocupado;
        using (var path = Camino(jugar, 10))
        using (var b = new System.Drawing.Drawing2D.LinearGradientBrush(jugar, sobre ? Acento2 : Acento, sobre ? Acento : Acento2, 0f))
            g.FillPath(b, path);
        Escribir(g, ocupado ? "ESPERÁ..." : "JUGAR  ▶", jugar.X + (jugar.Width - Medir(g, ocupado ? "ESPERÁ..." : "JUGAR  ▶", 14f, FontStyle.Bold)) / 2, jugar.Y + 12, 14f, FontStyle.Bold, Color.White);
        if (!ocupado) zonas.Add(new Zona { R = jugar, Click = Jugar });
    }

    // ---------- piezas ----------

    void Pildora(Graphics g, Rectangle r, string texto, bool activa, Action click)
    {
        bool sobre = r.Contains(mouse);
        Color relleno = activa ? Color.FromArgb(220, Acento) : Color.FromArgb(sobre ? 200 : 150, 30, 34, 46);
        Redondeado(g, r, r.Height / 2, relleno, activa ? Color.Empty : Color.FromArgb(sobre ? 120 : 60, 255, 255, 255));
        int w = Medir(g, texto, 9.5f, FontStyle.Bold);
        Escribir(g, texto, r.X + (r.Width - w) / 2, r.Y + (r.Height - 18) / 2, 9.5f, FontStyle.Bold, activa ? Oscuro : Texto);
        zonas.Add(new Zona { R = r, Click = click });
    }

    void Icono(Graphics g, Rectangle r, string texto, Action click)
    {
        bool sobre = r.Contains(mouse);
        Redondeado(g, r, 8, Color.FromArgb(sobre ? 200 : 130, 30, 34, 46), Color.FromArgb(60, 255, 255, 255));
        int w = Medir(g, texto, 10f, FontStyle.Bold);
        Escribir(g, texto, r.X + (r.Width - w) / 2, r.Y + (r.Height - 19) / 2, 10f, FontStyle.Bold, Texto);
        zonas.Add(new Zona { R = r, Click = click });
    }

    void Estado(Graphics g, int x, int y, string que, Color color, string valor)
    {
        Punto(g, x + 4, y + 10, color);
        Escribir(g, que, x + 16, y + 1, 9.5f, FontStyle.Regular, Texto);
        Escribir(g, valor, x + 160, y + 1, 9.5f, FontStyle.Bold, color);
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

    static System.Drawing.Drawing2D.GraphicsPath Camino(Rectangle r, int radio)
    {
        var p = new System.Drawing.Drawing2D.GraphicsPath();
        int d = Math.Max(1, Math.Min(radio * 2, Math.Min(r.Width, r.Height)));
        p.AddArc(r.X, r.Y, d, d, 180, 90);
        p.AddArc(r.Right - d, r.Y, d, d, 270, 90);
        p.AddArc(r.Right - d, r.Bottom - d, d, d, 0, 90);
        p.AddArc(r.X, r.Bottom - d, d, d, 90, 90);
        p.CloseFigure();
        return p;
    }

    static void Redondeado(Graphics g, Rectangle r, int radio, Color relleno, Color borde)
    {
        using (var p = Camino(r, radio))
        {
            using (var b = new SolidBrush(relleno)) g.FillPath(b, p);
            if (borde != Color.Empty) using (var l = new Pen(borde)) g.DrawPath(l, p);
        }
    }

    static void Escribir(Graphics g, string texto, int x, int y, float tam, FontStyle estilo, Color c)
    {
        using (var f = new Font("Segoe UI", tam, estilo))
        using (var b = new SolidBrush(c))
            g.DrawString(texto, f, b, x, y);
    }

    static int Medir(Graphics g, string texto, float tam, FontStyle estilo)
    {
        using (var f = new Font("Segoe UI", tam, estilo)) return (int)g.MeasureString(texto, f).Width;
    }

    static string Recortar(Graphics g, string texto, int ancho, float tam)
    {
        if (Medir(g, texto, tam, FontStyle.Regular) <= ancho) return texto;
        while (texto.Length > 1 && Medir(g, "..." + texto, tam, FontStyle.Regular) > ancho) texto = texto.Substring(1);
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

// Fondo: fondo.jpg del repo si existe (se guarda para abrir rápido la próxima vez); si no, uno dibujado acá.
static class Fondo
{
    const int MaxBytes = 15 * 1024 * 1024;

    static string Cache()
    {
        return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "AmericaRP", "fondo.jpg");
    }

    static Image Desde(byte[] datos)
    {
        // Se copia a un Bitmap para no depender del stream.
        using (var ms = new MemoryStream(datos))
        using (Image img = Image.FromStream(ms))
            return new Bitmap(img);
    }

    public static Image Cargado()
    {
        try { return File.Exists(Cache()) ? Desde(File.ReadAllBytes(Cache())) : null; }
        catch (Exception) { return null; }
    }

    public static Image Bajar()
    {
        if (Config.FondoUrl.Length == 0) return null;
        try
        {
            byte[] datos;
            using (var web = new WebClient()) datos = web.DownloadData(Config.FondoUrl);
            if (datos.Length > MaxBytes) return null;
            Image img = Desde(datos);
            Directory.CreateDirectory(Path.GetDirectoryName(Cache()));
            File.WriteAllBytes(Cache(), datos);
            return img;
        }
        catch (Exception) { return null; }
    }

    // Atardecer sobre una ciudad: siempre el mismo dibujo (semilla fija).
    public static Image Generado(int ancho, int alto)
    {
        var bmp = new Bitmap(ancho, alto);
        using (Graphics g = Graphics.FromImage(bmp))
        {
            g.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;
            int horizonte = (int)(alto * 0.72);
            using (var cielo = new System.Drawing.Drawing2D.LinearGradientBrush(new Rectangle(0, 0, ancho, horizonte + 1), Color.Black, Color.Black, 90f))
            {
                var mezcla = new System.Drawing.Drawing2D.ColorBlend();
                mezcla.Colors = new[] { Color.FromArgb(10, 12, 30), Color.FromArgb(52, 26, 72), Color.FromArgb(170, 60, 70), Color.FromArgb(245, 150, 60) };
                mezcla.Positions = new[] { 0f, 0.45f, 0.78f, 1f };
                cielo.InterpolationColors = mezcla;
                g.FillRectangle(cielo, 0, 0, ancho, horizonte + 1);
            }
            int sx = (int)(ancho * 0.68), sy = horizonte - 30;
            for (int i = 6; i >= 1; i--)
                using (var b = new SolidBrush(Color.FromArgb(18, 255, 190, 110))) g.FillEllipse(b, sx - 60 * i / 2 - 40, sy - 60 * i / 2 - 40, 60 * i + 80, 60 * i + 80);
            using (var b = new SolidBrush(Color.FromArgb(255, 214, 140))) g.FillEllipse(b, sx - 70, sy - 70, 140, 140);

            var azar = new Random(7);
            for (int capa = 0; capa < 2; capa++)
            {
                Color color = capa == 0 ? Color.FromArgb(40, 22, 44) : Color.FromArgb(14, 12, 22);
                int x = -20;
                while (x < ancho)
                {
                    int w = azar.Next(40, 110), h = azar.Next(capa == 0 ? 60 : 30, capa == 0 ? 260 : 190);
                    using (var b = new SolidBrush(color)) g.FillRectangle(b, x, horizonte - h + capa * 40, w, h + alto);
                    if (capa == 1)
                        for (int vy = horizonte - h + 52; vy < alto; vy += 14)
                            for (int vx = x + 8; vx < x + w - 8; vx += 12)
                                if (azar.Next(9) == 0)
                                    using (var v = new SolidBrush(Color.FromArgb(160, 255, 200, 120))) g.FillRectangle(v, vx, vy, 4, 6);
                    x += w + azar.Next(0, 12);
                }
            }
        }
        return bmp;
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
        }
        finally { Directory.Delete(carpeta, true); }

        Ver(Instalacion.NickValido.IsMatch("Juan_Perez") && !Instalacion.NickValido.IsMatch("ab") && !Instalacion.NickValido.IsMatch("con espacio"), "nick");
        Console.WriteLine(fallas == 0 ? "Todo bien." : fallas + " falla(s).");
        return fallas == 0 ? 0 : 1;
    }
}
