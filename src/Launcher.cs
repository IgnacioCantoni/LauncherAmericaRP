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

    // Devuelve cuántos archivos bajó. Si algo falla, tira la excepción y no deja archivos a medias.
    public static int Aplicar(string carpetaGta, string manifiestoUrl, Action<string, int> progreso)
    {
        using (var web = new WebClient())
        {
            web.Encoding = Encoding.UTF8;
            progreso("Buscando actualizaciones...", 0);
            var entradas = LeerManifiesto(web.DownloadString(manifiestoUrl));
            var pendientes = new List<KeyValuePair<string, string>>();
            for (int i = 0; i < entradas.Count; i++)
            {
                string destino = RutaSegura(carpetaGta, entradas[i].Value);
                progreso("Revisando " + entradas[i].Value, 100 * i / Math.Max(1, entradas.Count));
                if (!File.Exists(destino) || Sha256(destino) != entradas[i].Key) pendientes.Add(entradas[i]);
            }
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
            progreso(pendientes.Count == 0 ? "Todo al día." : "Actualizado: " + pendientes.Count + " archivo(s).", 100);
            return pendientes.Count;
        }
    }
}

class Ventana : Form
{
    static readonly Color Fondo = Color.FromArgb(18, 20, 26), Panel = Color.FromArgb(30, 34, 43),
        Acento = Color.FromArgb(232, 137, 43), Texto = Color.FromArgb(232, 234, 240), Gris = Color.FromArgb(150, 156, 170),
        Verde = Color.FromArgb(90, 200, 120), Rojo = Color.FromArgb(230, 90, 90);

    readonly TextBox nick = new TextBox(), noticias = new TextBox();
    readonly Label estadoServer = new Label(), carpetaGta = new Label(), estado = new Label();
    readonly Button jugar = new Button(), revisar = new Button(), elegir = new Button();
    readonly ProgressBar barra = new ProgressBar();
    readonly Timer reloj = new Timer();
    bool consultando, ocupado;

    public Ventana()
    {
        Text = "AMERICA RP";
        ClientSize = new Size(780, 470);
        FormBorderStyle = FormBorderStyle.FixedSingle;
        MaximizeBox = false;
        StartPosition = FormStartPosition.CenterScreen;
        BackColor = Fondo;
        ForeColor = Texto;
        Font = new Font("Segoe UI", 10f);
        try { Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath); } catch (Exception) { }

        Controls.Add(Etiqueta("AMERICA RP", 24, 18, 22f, FontStyle.Bold, Acento));
        Controls.Add(Etiqueta("Roleplay en español · " + Config.Host + ":" + Config.Puerto, 28, 62, 9.5f, FontStyle.Regular, Gris));
        Ubicar(estadoServer, 440, 30, 316, 40);
        estadoServer.TextAlign = ContentAlignment.MiddleRight;
        estadoServer.Text = "Consultando el server...";
        estadoServer.ForeColor = Gris;

        Controls.Add(Etiqueta("Novedades", 24, 100, 11f, FontStyle.Bold, Texto));
        Ubicar(noticias, 24, 128, 460, 270);
        noticias.Multiline = true;
        noticias.ReadOnly = true;
        noticias.ScrollBars = ScrollBars.Vertical;
        noticias.BorderStyle = BorderStyle.None;
        noticias.BackColor = Panel;
        noticias.ForeColor = Texto;
        noticias.Text = Config.NoticiasUrl.Length == 0 ? "Todavía no hay noticias configuradas." : "Cargando noticias...";

        Controls.Add(Etiqueta("Tu nick", 508, 100, 11f, FontStyle.Bold, Texto));
        Ubicar(nick, 508, 128, 248, 28);
        nick.MaxLength = 20;
        nick.BackColor = Panel;
        nick.ForeColor = Texto;
        nick.BorderStyle = BorderStyle.FixedSingle;
        nick.Text = Registro.Nick;

        Boton(jugar, "JUGAR", 508, 172, 248, 56, Acento, Fondo, 14f);
        Boton(revisar, "Revisar instalación", 508, 240, 248, 36, Panel, Texto, 10f);
        Boton(elegir, "Elegir carpeta del GTA...", 508, 286, 248, 36, Panel, Texto, 10f);
        Ubicar(carpetaGta, 508, 330, 248, 68);
        carpetaGta.ForeColor = Gris;
        carpetaGta.Font = new Font("Segoe UI", 8.5f);
        MostrarCarpeta();

        Ubicar(barra, 24, 414, 732, 10);
        Ubicar(estado, 24, 430, 732, 24);
        estado.ForeColor = Gris;
        estado.Text = "Listo.";

        jugar.Click += delegate { Jugar(); };
        revisar.Click += delegate { Revisar(); };
        elegir.Click += delegate { ElegirCarpeta(); };
        AcceptButton = jugar;
        reloj.Interval = 15000;
        reloj.Tick += delegate { RefrescarServer(); };
        ActiveControl = nick;
        Shown += delegate { reloj.Start(); RefrescarServer(); CargarNoticias(); };
    }

    Label Etiqueta(string texto, int x, int y, float tam, FontStyle estilo, Color color)
    {
        return new Label { Text = texto, Location = new Point(x, y), AutoSize = true, ForeColor = color, Font = new Font("Segoe UI", tam, estilo) };
    }

    void Ubicar(Control c, int x, int y, int ancho, int alto)
    {
        c.Location = new Point(x, y);
        c.Size = new Size(ancho, alto);
        Controls.Add(c);
    }

    void Boton(Button b, string texto, int x, int y, int ancho, int alto, Color fondo, Color letra, float tam)
    {
        b.Text = texto;
        b.FlatStyle = FlatStyle.Flat;
        b.FlatAppearance.BorderSize = 0;
        b.BackColor = fondo;
        b.ForeColor = letra;
        b.Font = new Font("Segoe UI", tam, FontStyle.Bold);
        b.Cursor = Cursors.Hand;
        Ubicar(b, x, y, ancho, alto);
    }

    string Carpeta()
    {
        string exe = Registro.GtaExe;
        return exe.Length == 0 ? "" : Path.GetDirectoryName(exe);
    }

    void MostrarCarpeta()
    {
        string c = Carpeta();
        carpetaGta.Text = c.Length == 0 ? "Carpeta del GTA sin elegir." : "GTA en: " + c;
    }

    void Avisar(string texto, int porcentaje)
    {
        if (InvokeRequired) { BeginInvoke(new Action<string, int>(Avisar), texto, porcentaje); return; }
        estado.Text = texto;
        barra.Value = Math.Max(0, Math.Min(100, porcentaje));
    }

    async void RefrescarServer()
    {
        if (consultando) return;
        consultando = true;
        EstadoServidor e = await Task.Run(() => Consulta.Pedir(Config.Host, Config.Puerto, 2500));
        consultando = false;
        estadoServer.ForeColor = e.EnLinea ? Verde : Rojo;
        estadoServer.Text = e.EnLinea
            ? "● En línea · " + e.Jugadores + "/" + e.Maximo + " jugadores · " + e.Ping + " ms"
            : "● Server apagado o sin respuesta";
    }

    async void CargarNoticias()
    {
        if (Config.NoticiasUrl.Length == 0) return;
        try
        {
            string texto = await Task.Run(() =>
            {
                using (var web = new WebClient()) { web.Encoding = Encoding.UTF8; return web.DownloadString(Config.NoticiasUrl); }
            });
            noticias.Text = texto.Replace("\r\n", "\n").Replace("\n", "\r\n");
        }
        catch (Exception ex) { noticias.Text = "No se pudieron cargar las noticias: " + ex.Message; }
    }

    bool ElegirCarpeta()
    {
        using (var d = new OpenFileDialog { Title = "Buscá gta_sa.exe", Filter = "GTA San Andreas|gta_sa.exe" })
        {
            if (d.ShowDialog(this) != DialogResult.OK) return false;
            Registro.GtaExe = d.FileName;
        }
        MostrarCarpeta();
        return true;
    }

    void Ocupar(bool si)
    {
        ocupado = si;
        jugar.Enabled = revisar.Enabled = elegir.Enabled = nick.Enabled = !si;
    }

    // Baja lo que cambió (si hay manifiesto) y dice qué falta. Devuelve true si se puede jugar.
    async Task<bool> Preparar()
    {
        string carpeta = Carpeta();
        if (Instalacion.Faltantes(carpeta).Count > 0 && carpeta.Length == 0 && !ElegirCarpeta()) return false;
        carpeta = Carpeta();
        if (Config.ManifiestoUrl.Length > 0 && File.Exists(Path.Combine(carpeta, "gta_sa.exe")))
        {
            try { await Task.Run(() => Actualizador.Aplicar(carpeta, Config.ManifiestoUrl, Avisar)); }
            catch (Exception ex)
            {
                Avisar("No se pudo actualizar.", 0);
                if (MessageBox.Show(this, ex.Message + "\n\n¿Seguir sin actualizar?", "Actualizaciones", MessageBoxButtons.YesNo, MessageBoxIcon.Warning) != DialogResult.Yes)
                    return false;
            }
        }
        List<string> faltan = Instalacion.Faltantes(carpeta);
        if (faltan.Count > 0)
        {
            Avisar(faltan[0], 0);
            bool sinSamp = faltan[0].Contains("SA-MP");
            string pregunta = string.Join("\n", faltan) + (sinSamp ? "\n\n¿Abrir la página para bajar SA-MP 0.3.7?" : "");
            if (MessageBox.Show(this, pregunta, "Instalación", sinSamp ? MessageBoxButtons.YesNo : MessageBoxButtons.OK, MessageBoxIcon.Warning) == DialogResult.Yes)
                Process.Start(Config.DescargaSampUrl);
            return false;
        }
        if (!Instalacion.PareceGta10(carpeta))
            Avisar("Tu gta_sa.exe no parece la versión 1.0. Si el juego se cierra al conectar, instalá la 1.0.", 100);
        return true;
    }

    async void Revisar()
    {
        if (ocupado) return;
        Ocupar(true);
        try
        {
            if (await Preparar() && Instalacion.PareceGta10(Carpeta())) Avisar("La instalación está bien.", 100);
        }
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
