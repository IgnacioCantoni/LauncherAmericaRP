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
using System.Runtime.InteropServices;
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
    // Versión de este launcher. Para sacar una nueva, ver "Sacar una versión nueva del launcher" en el README.
    public const string Version = "1.3.1";
    public const string Host = "127.0.0.1";
    public const int Puerto = 7777;
    // Vacío = sin noticias / sin actualizaciones.
    const string Repo = "https://raw.githubusercontent.com/IgnacioCantoni/LauncherAmericaRP/main/";
    public const string NoticiasUrl = Repo + "noticias.txt";
    public const string ManifiestoUrl = Repo + "actualizaciones/manifiesto.txt";
    // El launcher se actualiza solo: launcher/version.txt dice la última versión y la huella de su .exe, que está en la
    // Release de GitHub con la etiqueta v<versión>. VersionUrl vacío = no se actualiza.
    public const string VersionUrl = Repo + "launcher/version.txt";
    // Archivos que no pueden estar en el GTA (cheats, mods rotos). Se revisa en cada JUGAR. Vacío = no se revisa.
    public const string ProhibidosUrl = Repo + "prohibidos.txt";
    public const string ExeUrl = "https://github.com/IgnacioCantoni/LauncherAmericaRP/releases/download/v{0}/AmericaRP.exe";
    public const string DescargasUrl = "https://github.com/IgnacioCantoni/LauncherAmericaRP/releases/latest";
    // DirectX 9 de junio de 2010, el instalador oficial de Microsoft (100.275.120 bytes, firmado por Microsoft). Trae las
    // d3dx9 que piden samp.dll (d3dx9_25) y el ENB (d3dx9_43), y que Windows 10 y 11 no traen. Vacío = no se ofrece.
    public const string DirectXUrl = "https://download.microsoft.com/download/8/4/A/84A35BF1-DAFE-4AE8-82AF-AD2AE20B6B14/directx_Jun2010_redist.exe";
    public const string DirectXSha = "053f76dcbb28802e23341b6a787e3b0791c0fa5c8d4d011b1044172dbf89c73b";
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
    // Pantallas en HTML del server (teléfono y las que vengan): cliente de omp-cef (licencia MIT). Su libcef.dll pesa
    // más de 100 MB y no entra en el repo: se baja el zip oficial del release y se revisa su huella. Vacío = no se instala.
    public const string CefZipUrl = "https://github.com/aurora-mp/omp-cef/releases/download/v1.4.0/client-files-v1.4.0.zip";
    public const string CefZipSha = "9bdcf634a6b473e648716deaa3779f55ac1211924ee9c55013897582cf34e55f";
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
        // Es la tabla de textos del juego: sin ella el SA-MP se cae al cargar sin decir por qué. Vale cualquier idioma.
        if (!File.Exists(Path.Combine(carpeta, "text", "american.gxt")))
            lista.Add("Falta text\\american.gxt en la carpeta del GTA: sin ese archivo el juego se cierra al cargar. Copialo de otro GTA San Andreas 1.0.");
        return lista;
    }

    // [carpeta, motivo, "grave" si Windows no deja escribir ahí sin ser administrador]
    public static List<string[]> LugaresMalos()
    {
        var l = new List<string[]>();
        string nada = "Windows no deja que el launcher actualice archivos ahí. Mové el GTA a otra carpeta, por ejemplo C:\\Juegos\\GTA San Andreas.";
        foreach (Environment.SpecialFolder f in new[] { Environment.SpecialFolder.ProgramFiles, Environment.SpecialFolder.ProgramFilesX86, Environment.SpecialFolder.Windows })
            l.Add(new[] { Environment.GetFolderPath(f), "El GTA está en " + Environment.GetFolderPath(f) + ". " + nada, "grave" });
        string onedrive = Environment.GetEnvironmentVariable("OneDrive") ?? "";
        l.Add(new[] { onedrive, "El GTA está en OneDrive: puede subir o borrar archivos mientras jugás. Conviene moverlo a otra carpeta.", "" });
        l.Add(new[] { Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), "El GTA está en el Escritorio: el antivirus lo revisa más y puede trabarlo. Conviene moverlo a otra carpeta.", "" });
        return l;
    }

    // null si la carpeta está bien.
    public static string[] ProblemaCarpeta(string carpeta, List<string[]> lugares)
    {
        if (string.IsNullOrEmpty(carpeta)) return null;
        string c = Path.GetFullPath(carpeta).TrimEnd('\\', '/') + Path.DirectorySeparatorChar;
        foreach (string[] l in lugares)
        {
            if (l[0].Length == 0) continue;
            string raiz = Path.GetFullPath(l[0]).TrimEnd('\\', '/') + Path.DirectorySeparatorChar;
            if (c.StartsWith(raiz, StringComparison.OrdinalIgnoreCase)) return l;
        }
        return null;
    }

    // Parche de 4 GB: el GTA es de 32 bits y sin la marca Large Address Aware Windows le da 2 GB. Con el ENB se queda sin
    // memoria a los 10 o 15 minutos y se cierra sin error. Devuelve true si lo puso (la primera vez guarda una copia).
    public static bool Poner4Gb(string exe)
    {
        byte[] d = File.ReadAllBytes(exe);
        if (d.Length < 0x40 || d[0] != 'M' || d[1] != 'Z') throw new InvalidDataException("gta_sa.exe no es un programa de Windows.");
        int pe = BitConverter.ToInt32(d, 0x3C);
        if (pe < 0 || pe + 24 > d.Length || d[pe] != 'P' || d[pe + 1] != 'E' || d[pe + 2] != 0 || d[pe + 3] != 0) throw new InvalidDataException("gta_sa.exe no es un programa de Windows.");
        int marcas = pe + 22; // Characteristics del encabezado COFF
        if ((d[marcas] & 0x20) != 0) return false;
        string copia = exe + ".sin4gb";
        if (!File.Exists(copia)) File.Copy(exe, copia);
        d[marcas] |= 0x20;
        File.WriteAllBytes(exe, d);
        return true;
    }

    public static bool PareceGta10(string carpeta)
    {
        long tam = new FileInfo(Path.Combine(carpeta, "gta_sa.exe")).Length;
        return TamanosGta10.Contains(tam);
    }
}

// Noticias: en noticias.txt cada "## fecha | etiqueta | título" abre una noticia y las líneas que siguen son su texto
// ("- " al principio = un punto de lista). Un archivo sin "## " se muestra entero como una sola noticia.
class Noticia { public string Fecha = "", Etiqueta = "", Titulo = ""; public List<string> Lineas = new List<string>(); }

static class Noticias
{
    public static List<Noticia> Leer(string texto)
    {
        var lista = new List<Noticia>();
        Noticia actual = null;
        foreach (string cruda in texto.Replace("\r", "").Split('\n'))
        {
            string l = cruda.TrimEnd();
            if (l.StartsWith("## "))
            {
                string[] p = l.Substring(3).Split('|').Select(x => x.Trim()).ToArray();
                actual = new Noticia();
                if (p.Length >= 3) { actual.Fecha = p[0]; actual.Etiqueta = p[1]; actual.Titulo = string.Join(" | ", p.Skip(2)); }
                else actual.Titulo = l.Substring(3).Trim();
                lista.Add(actual);
                continue;
            }
            if (actual == null)
            {
                if (l.Length == 0) continue;
                actual = new Noticia();
                lista.Add(actual);
            }
            actual.Lineas.Add(l);
        }
        foreach (Noticia n in lista)
            while (n.Lineas.Count > 0 && n.Lineas[n.Lineas.Count - 1].Length == 0) n.Lineas.RemoveAt(n.Lineas.Count - 1);
        return lista;
    }
}

// Ajustes del jugador, en %LOCALAPPDATA%\AmericaRP\ajustes.txt (una línea clave=valor por ajuste).
static class Ajustes
{
    public static string Ruta = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "AmericaRP", "ajustes.txt");

    static Dictionary<string, string> Leer()
    {
        var d = new Dictionary<string, string>();
        try
        {
            if (File.Exists(Ruta))
                foreach (string l in File.ReadAllLines(Ruta))
                {
                    int i = l.IndexOf('=');
                    if (i > 0) d[l.Substring(0, i).Trim()] = l.Substring(i + 1).Trim();
                }
        }
        catch (Exception) { }
        return d;
    }

    static bool Si(string clave, bool porDefecto)
    {
        string v;
        return Leer().TryGetValue(clave, out v) ? v == "si" : porDefecto;
    }

    static void Poner(string clave, bool valor)
    {
        Dictionary<string, string> d = Leer();
        d[clave] = valor ? "si" : "no";
        try
        {
            Directory.CreateDirectory(Path.GetDirectoryName(Ruta));
            File.WriteAllLines(Ruta, d.Select(e => e.Key + "=" + e.Value));
        }
        catch (Exception) { }
    }

    // Mientras jugás el launcher se va a la bandeja (al lado del reloj) en vez de quedar minimizado.
    public static bool Bandeja { get { return Si("bandeja", true); } set { Poner("bandeja", value); } }
    // Si hay una versión nueva del launcher, se instala sin preguntar.
    public static bool ActualizarSolo { get { return Si("actualizar_solo", false); } set { Poner("actualizar_solo", value); } }
}

// Informe para pegar en el canal de soporte: lo que soporte siempre pregunta, en un solo texto.
static class Soporte
{
    public static string DirInformes() { return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "AmericaRP", "informes"); }

    // El encabezado del último informe de cierre (sin el chat), o "" si no hay.
    public static string UltimoCierre(string dir)
    {
        if (!Directory.Exists(dir)) return "";
        string ultimo = Directory.GetFiles(dir, "cierre-*.txt").OrderBy(f => Path.GetFileName(f), StringComparer.Ordinal).LastOrDefault();
        if (ultimo == null) return "";
        return string.Join("\n", File.ReadAllLines(ultimo).Skip(1).TakeWhile(l => l.Trim().Length > 0));
    }

    public static string Armar(List<string[]> filas, string carpeta, string nick, bool enb, string ultimoCierre)
    {
        var sb = new StringBuilder();
        sb.AppendLine("**AMERICA RP · informe para soporte**");
        sb.AppendLine("Fecha: " + DateTime.Now.ToString("yyyy-MM-dd HH:mm"));
        sb.AppendLine("Launcher: " + Config.Version);
        sb.AppendLine("Nick: " + (nick.Length == 0 ? "-" : nick));
        sb.AppendLine("Windows: " + Environment.OSVersion.VersionString + (Environment.Is64BitOperatingSystem ? ", 64 bits" : ", 32 bits"));
        sb.AppendLine("Carpeta del GTA: " + (carpeta.Length == 0 ? "sin elegir" : carpeta));
        foreach (string[] f in filas) sb.AppendLine(f[0] + ": " + f[1]);
        sb.AppendLine("ENB: " + (enb ? "activo" : "no"));
        sb.AppendLine("Último cierre de golpe: " + (ultimoCierre.Length == 0 ? "ninguno" : "\n" + ultimoCierre));
        return sb.ToString();
    }
}

// prohibidos.txt: cada línea es una ruta dentro del GTA, con * y ? de comodines (sin "/" vale para cualquier carpeta),
// o una huella SHA-256 de 64 letras, para atrapar el archivo aunque le cambien el nombre. "#" empieza un comentario.
// Lo que coincide no se borra: se mueve a _prohibidos\<fecha> dentro del GTA.
static class Prohibidos
{
    public const string Carpeta = "_prohibidos";
    // Solo se les saca la huella a estos (los cheats son scripts o dll); los .img de 1 GB no se leen.
    static readonly string[] ConHuella = { ".cs", ".cleo", ".asi", ".dll", ".lua", ".luac", ".exe", ".sf" };
    // Lo que el juego necesita no se saca nunca, aunque una regla mal escrita lo agarre.
    static readonly string[] Base = { "gta_sa.exe", "samp.exe", "samp.dll", "vorbisfile.dll", "vorbis.dll", "eax.dll", "ogg.dll" };

    public class Lista { public List<Regex> Rutas = new List<Regex>(); public HashSet<string> Huellas = new HashSet<string>(); }

    public static Lista Leer(string texto)
    {
        var l = new Lista();
        foreach (string cruda in texto.Replace("\r", "").Split('\n'))
        {
            int c = cruda.IndexOf('#');
            string r = (c >= 0 ? cruda.Substring(0, c) : cruda).Trim().Replace('\\', '/').TrimStart('/');
            if (r.Length == 0 || r.Contains("..")) continue;
            if (Regex.IsMatch(r, "^[0-9a-fA-F]{64}$")) { l.Huellas.Add(r.ToLowerInvariant()); continue; }
            string patron = Regex.Escape(r).Replace("\\*", "[^/]*").Replace("\\?", "[^/]");
            l.Rutas.Add(new Regex((r.Contains("/") ? "^" : "(^|/)") + patron + "$", RegexOptions.IgnoreCase | RegexOptions.CultureInvariant));
        }
        return l;
    }

    // Rutas (con "/", relativas al GTA) que la lista prohíbe. protegidos: lo que reparte el launcher, que nunca se saca.
    public static List<string> Buscar(string carpetaGta, Lista lista, IEnumerable<string> protegidos)
    {
        var encontrados = new List<string>();
        if (lista.Rutas.Count == 0 && lista.Huellas.Count == 0) return encontrados;
        var cuidar = new HashSet<string>(Base.Concat(protegidos).Select(x => x.Replace('\\', '/').ToLowerInvariant()));
        var pendientes = new Stack<string>();
        pendientes.Push(carpetaGta);
        while (pendientes.Count > 0)
        {
            string dir = pendientes.Pop();
            string[] archivos, carpetas;
            try { archivos = Directory.GetFiles(dir); carpetas = Directory.GetDirectories(dir); }
            catch (Exception) { continue; }
            foreach (string sub in carpetas)
                if (!string.Equals(Path.GetFileName(sub), Carpeta, StringComparison.OrdinalIgnoreCase) || dir != carpetaGta) pendientes.Push(sub);
            foreach (string f in archivos)
            {
                string ruta = f.Substring(carpetaGta.Length).TrimStart('\\', '/').Replace('\\', '/');
                if (cuidar.Contains(ruta.ToLowerInvariant())) continue;
                bool malo = lista.Rutas.Any(r => r.IsMatch(ruta));
                if (!malo && lista.Huellas.Count > 0 && ConHuella.Contains(Path.GetExtension(f).ToLowerInvariant()))
                {
                    try { malo = new FileInfo(f).Length < 50000000 && lista.Huellas.Contains(Actualizador.HuellaRapida(f)); }
                    catch (Exception) { }
                }
                if (malo) encontrados.Add(ruta);
            }
        }
        encontrados.Sort(StringComparer.OrdinalIgnoreCase);
        return encontrados;
    }

    // Mueve cada archivo a _prohibidos\<fecha>\<ruta>. Devuelve la carpeta donde quedaron.
    public static string Sacar(string carpetaGta, List<string> rutas)
    {
        string destino = Path.Combine(carpetaGta, Carpeta, DateTime.Now.ToString("yyyyMMdd-HHmmss"));
        foreach (string ruta in rutas)
        {
            string nuevo = Path.Combine(destino, ruta.Replace('/', Path.DirectorySeparatorChar));
            Directory.CreateDirectory(Path.GetDirectoryName(nuevo));
            if (File.Exists(nuevo)) nuevo += "." + Guid.NewGuid().ToString("N").Substring(0, 6);
            File.Move(Path.Combine(carpetaGta, ruta.Replace('/', Path.DirectorySeparatorChar)), nuevo);
        }
        return destino;
    }
}

// Lo que pasa con el GTA después de JUGAR: si se cerró bien o de golpe, y el informe para soporte.
static class Juego
{
    [DllImport("kernel32.dll", SetLastError = true)] static extern IntPtr OpenProcess(uint acceso, bool heredar, int id);
    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)] static extern bool QueryFullProcessImageName(IntPtr h, int formato, StringBuilder ruta, ref int largo);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
    delegate bool CadaVentana(IntPtr v, IntPtr dato);
    [DllImport("user32.dll")] static extern bool EnumWindows(CadaVentana f, IntPtr dato);
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr v, out int id);
    [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr v);
    [DllImport("user32.dll")] static extern bool SetForegroundWindow(IntPtr v);
    [DllImport("user32.dll")] static extern bool AllowSetForegroundWindow(int id);

    // Con dos monitores el GTA abre "Device Selection" (elegir pantalla) sin botón en la barra de tareas. Si el launcher
    // se esconde antes, Windows le da el foco a otra ventana y ese cuadro queda tapado: el juego parece no abrir nunca.
    // Por eso el launcher espera la primera ventana del GTA (hasta un minuto), la trae al frente y recién ahí se esconde.
    public static void DejarPasarAlFrente() { AllowSetForegroundWindow(-1); }

    public static IntPtr EsperarVentana(string carpeta)
    {
        string exe = Path.Combine(Path.GetFullPath(carpeta), "gta_sa.exe");
        for (int i = 0; i < 120; i++)
        {
            var ids = new HashSet<int>();
            foreach (Process p in Process.GetProcessesByName("gta_sa"))
                using (p) if (string.Equals(Ruta(p.Id), exe, StringComparison.OrdinalIgnoreCase)) ids.Add(p.Id);
            IntPtr hallada = IntPtr.Zero;
            if (ids.Count > 0)
                EnumWindows(delegate (IntPtr v, IntPtr dato)
                {
                    int id;
                    GetWindowThreadProcessId(v, out id);
                    if (ids.Contains(id) && IsWindowVisible(v)) { hallada = v; return false; }
                    return true;
                }, IntPtr.Zero);
            if (hallada != IntPtr.Zero) return hallada;
            System.Threading.Thread.Sleep(500);
        }
        return IntPtr.Zero;
    }

    public static void AlFrente(IntPtr v) { SetForegroundWindow(v); }

    public class Cierre { public int? Codigo; public DateTime Inicio, Fin; public bool Bien { get { return Codigo == null || Codigo == 0; } } }

    // Ruta completa del .exe de un proceso, también de uno de 32 bits (Process.MainModule no siempre puede).
    static string Ruta(int id)
    {
        IntPtr h = OpenProcess(0x1000, false, id); // PROCESS_QUERY_LIMITED_INFORMATION
        if (h == IntPtr.Zero) return null;
        try
        {
            var sb = new StringBuilder(1024);
            int n = sb.Capacity;
            return QueryFullProcessImageName(h, 0, sb, ref n) ? sb.ToString() : null;
        }
        finally { CloseHandle(h); }
    }

    public static bool Abierto() { return Process.GetProcessesByName("gta_sa").Length > 0; }

    // Para un GTA trabado (por ejemplo, en la ventana de elegir resolución escondida detrás de todo).
    public static void Cerrar()
    {
        foreach (Process p in Process.GetProcessesByName("gta_sa"))
            using (p)
            {
                try { p.Kill(); p.WaitForExit(5000); } catch (Exception) { }
            }
    }

    // Espera a que el samp.exe abra el GTA (hasta un minuto) y después a que se cierre. null si nunca apareció.
    public static Cierre Esperar(string carpeta, DateTime inicio)
    {
        string exe = Path.Combine(Path.GetFullPath(carpeta), "gta_sa.exe");
        Process gta = null;
        for (int i = 0; i < 120 && gta == null; i++)
        {
            foreach (Process p in Process.GetProcessesByName("gta_sa"))
                if (gta == null && string.Equals(Ruta(p.Id), exe, StringComparison.OrdinalIgnoreCase)) gta = p; else p.Dispose();
            if (gta == null) System.Threading.Thread.Sleep(500);
        }
        if (gta == null) return null;
        using (gta)
        {
            gta.WaitForExit();
            var c = new Cierre { Inicio = inicio, Fin = DateTime.Now };
            try { c.Codigo = gta.ExitCode; } catch (Exception) { } // sin permiso para leerlo: no se avisa nada
            return c;
        }
    }

    // El CEF deja procesos (cef\renderer.exe) que a veces siguen vivos si el GTA se cerró mal, con sus archivos trabados.
    public static int CerrarCefColgado(string carpeta)
    {
        string cef = Path.Combine(Path.GetFullPath(carpeta), "cef") + Path.DirectorySeparatorChar;
        int n = 0;
        foreach (Process p in Process.GetProcesses())
            using (p)
            {
                string ruta = Ruta(p.Id);
                if (ruta == null || !ruta.StartsWith(cef, StringComparison.OrdinalIgnoreCase)) continue;
                try { p.Kill(); n++; } catch (Exception) { }
            }
        return n;
    }

    public static string CodigoTexto(int codigo)
    {
        string hex = "0x" + ((uint)codigo).ToString("X8");
        switch ((uint)codigo)
        {
            case 0xC0000005: return hex + " (acceso a memoria inválido: casi siempre un mod o falta de memoria)";
            case 0xC00000FD: return hex + " (se quedó sin pila)";
            case 0xC0000602: return hex + " (falla al cerrar el CEF: revisá que esté salida_limpia.asi)";
            case 0xC0000409: return hex + " (un programa rompió su propia memoria)";
            case 0xE06D7363: return hex + " (error dentro de un .asi o .dll)";
            case 1: return hex + " (lo cerraron desde el Administrador de tareas o se trabó)";
            default: return hex;
        }
    }

    public static string Informe(Cierre c, string carpeta, bool enb, string[] log)
    {
        var sb = new StringBuilder();
        sb.AppendLine("AMERICA RP: el GTA se cerró de golpe");
        sb.AppendLine("Fecha: " + c.Fin.ToString("yyyy-MM-dd HH:mm:ss"));
        sb.AppendLine("Launcher: " + Config.Version);
        sb.AppendLine("Código de salida: " + (c.Codigo == null ? "desconocido" : CodigoTexto(c.Codigo.Value)));
        sb.AppendLine("Tiempo jugado: " + (int)(c.Fin - c.Inicio).TotalMinutes + " min");
        sb.AppendLine("Carpeta del GTA: " + carpeta);
        sb.AppendLine("ENB activo: " + (enb ? "sí" : "no"));
        sb.AppendLine("Windows: " + Environment.OSVersion.VersionString + (Environment.Is64BitOperatingSystem ? ", 64 bits" : ", 32 bits"));
        sb.AppendLine();
        sb.AppendLine("Últimas líneas del chat de SA-MP:");
        foreach (string l in log) sb.AppendLine(l);
        return sb.ToString();
    }

    // Las últimas líneas de un archivo que puede estar abierto por otro programa.
    public static string[] Ultimas(string archivo, int cuantas)
    {
        if (!File.Exists(archivo)) return new string[0];
        using (var f = new FileStream(archivo, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete))
        using (var r = new StreamReader(f, Consulta.Texto1252()))
        {
            var cola = new Queue<string>();
            string l;
            while ((l = r.ReadLine()) != null) { cola.Enqueue(l); if (cola.Count > cuantas) cola.Dequeue(); }
            return cola.ToArray();
        }
    }

    // Guarda el informe en %LOCALAPPDATA%\AmericaRP\informes y devuelve la ruta.
    public static string GuardarInforme(Cierre c, string carpeta, bool enb)
    {
        string chat = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "GTA San Andreas User Files", "SAMP", "chatlog.txt");
        string dir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "AmericaRP", "informes");
        Directory.CreateDirectory(dir);
        string archivo = Path.Combine(dir, "cierre-" + c.Fin.ToString("yyyyMMdd-HHmmss") + ".txt");
        File.WriteAllText(archivo, Informe(c, carpeta, enb, Ultimas(chat, 30)), new UTF8Encoding(true));
        return archivo;
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

    // Memoria de huellas: si un archivo tiene el mismo tamaño y la misma fecha que la última vez, no se vuelve a leer.
    // shortcut: quien cambie un archivo dejando igual el tamaño y la fecha no se detecta; si hace falta, hashear todo al cambiar de versión.
    public static string CacheRuta = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "AmericaRP", "huellas.txt");
    static readonly object candado = new object();
    static Dictionary<string, string> cache;

    public static string HuellaRapida(string archivo)
    {
        var fi = new FileInfo(archivo);
        string clave = fi.FullName.ToLowerInvariant(), marca = fi.Length + " " + fi.LastWriteTimeUtc.Ticks + " ";
        lock (candado)
        {
            if (cache == null) cache = LeerCache();
            string v;
            if (cache.TryGetValue(clave, out v) && v.StartsWith(marca)) return v.Substring(marca.Length);
        }
        string sha = Sha256(archivo);
        lock (candado)
        {
            cache[clave] = marca + sha;
            try
            {
                Directory.CreateDirectory(Path.GetDirectoryName(CacheRuta));
                File.WriteAllLines(CacheRuta, cache.Select(e => e.Key + "\t" + e.Value));
            }
            catch (Exception) { } // sin memoria se revisa todo la próxima vez, nada más
        }
        return sha;
    }

    public static void OlvidarHuellas() { lock (candado) cache = null; }

    static Dictionary<string, string> LeerCache()
    {
        var d = new Dictionary<string, string>();
        try
        {
            if (File.Exists(CacheRuta))
                foreach (string l in File.ReadAllLines(CacheRuta))
                {
                    int t = l.IndexOf('\t');
                    if (t > 0) d[l.Substring(0, t)] = l.Substring(t + 1);
                }
        }
        catch (Exception) { }
        return d;
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
            if (!File.Exists(destino) || HuellaRapida(destino) != r.Entradas[i].Key) r.Pendientes.Add(r.Entradas[i].Value);
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

    // Instala el cliente de CEF si falta o es de otra versión. Devuelve false si ya estaba.
    public static bool InstalarCef(string carpetaGta, Action<string, int> progreso)
    {
        string marca = RutaSegura(carpetaGta, "cef/americarp-version.txt");
        if (File.Exists(marca) && File.ReadAllText(marca).Trim() == Config.CefZipSha && File.Exists(RutaSegura(carpetaGta, "cef.asi")))
            return false;
        string zip = Path.Combine(Path.GetTempPath(), "AmericaRP-cef.zip");
        try
        {
            Bajar(Config.CefZipUrl, zip, "Bajando las pantallas del server", progreso);
            if (Sha256(zip) != Config.CefZipSha) throw new InvalidDataException("El cliente de CEF bajado no es el esperado.");
            progreso("Instalando las pantallas del server...", 100);
            ExtraerCef(carpetaGta, zip);
            File.WriteAllText(marca, Config.CefZipSha);
        }
        finally { if (File.Exists(zip)) File.Delete(zip); }
        return true;
    }

    // Del zip de omp-cef solo van cef.asi y la carpeta cef/ (sin el .lib, que es para compilar).
    public static void ExtraerCef(string carpetaGta, string zip)
    {
        using (ZipArchive z = ZipFile.OpenRead(zip))
            foreach (ZipArchiveEntry e in z.Entries)
            {
                string nombre = e.FullName.Replace('\\', '/');
                if (e.Name.Length == 0 || nombre.EndsWith(".lib") || (nombre != "cef.asi" && !nombre.StartsWith("cef/"))) continue;
                string destino = RutaSegura(carpetaGta, nombre);
                Directory.CreateDirectory(Path.GetDirectoryName(destino));
                try { e.ExtractToFile(destino, true); }
                catch (IOException) { throw new IOException("No se pudo reemplazar " + nombre + ". Cerrá el GTA y probá de nuevo."); }
            }
    }

    // Descarga con avance, para archivos grandes.
    public static void Bajar(string url, string destino, string texto, Action<string, int> progreso)
    {
        using (WebResponse respuesta = WebRequest.Create(url).GetResponse())
        using (Stream entrada = respuesta.GetResponseStream())
        using (FileStream salida = File.Create(destino))
        {
            long total = respuesta.ContentLength, leido = 0;
            byte[] buffer = new byte[81920];
            int n, ultimo = -1;
            while ((n = entrada.Read(buffer, 0, buffer.Length)) > 0)
            {
                salida.Write(buffer, 0, n);
                leido += n;
                int porcentaje = total > 0 ? (int)(100 * leido / total) : 0;
                if (porcentaje != ultimo)
                {
                    ultimo = porcentaje;
                    progreso(texto + ": " + (leido >> 20) + (total > 0 ? " de " + (total >> 20) : "") + " MB", porcentaje);
                }
            }
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
                    if (!File.Exists(temporal))
                        throw new IOException("El antivirus borró " + ruta + " apenas se bajó. Si confiás en el server, permitilo en el historial de protección de Windows.");
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

// El launcher se actualiza solo (ver Config.VersionUrl).
static class Autoactualizacion
{
    // launcher/version.txt: "1.2.0 <sha256 del AmericaRP.exe>".
    public static KeyValuePair<Version, string> Leer(string texto)
    {
        string[] p = texto.Trim().Split(' ');
        Version v;
        if (p.Length != 2 || !Version.TryParse(p[0], out v) || !Regex.IsMatch(p[1], "^[0-9a-f]{64}$"))
            throw new InvalidDataException("launcher/version.txt no tiene el formato esperado.");
        return new KeyValuePair<Version, string>(v, p[1]);
    }

    public static string Linea(string exe) { return Config.Version + " " + Actualizador.Sha256(exe) + "\n"; }

    // Windows deja renombrar un .exe que está corriendo pero no pisarlo: el actual pasa a .viejo y el nuevo toma su lugar.
    public static void Reemplazar(string exe, string nuevo)
    {
        string viejo = exe + ".viejo";
        if (File.Exists(viejo)) File.Delete(viejo);
        File.Move(exe, viejo);
        try { File.Move(nuevo, exe); }
        catch (Exception) { File.Move(viejo, exe); throw; }
    }

    // El .viejo queda hasta el próximo arranque, porque mientras corría no se podía borrar.
    public static void BorrarViejo(string exe) { try { File.Delete(exe + ".viejo"); } catch (Exception) { } }

    public static void Instalar(string exe, Version v, string sha, Action<string, int> progreso)
    {
        string nuevo = exe + ".nuevo";
        try
        {
            Actualizador.Bajar(string.Format(Config.ExeUrl, v), nuevo, "Bajando el launcher " + v, progreso);
            if (Actualizador.Sha256(nuevo) != sha) throw new InvalidDataException("El launcher bajado no es el esperado.");
            Reemplazar(exe, nuevo);
        }
        finally { if (File.Exists(nuevo)) File.Delete(nuevo); }
    }
}

// DirectX 9: Windows trae d3d9.dll pero no las d3dx9_*.dll, que vienen con el instalador de junio de 2010.
static class DirectX
{
    // Las que faltan, ni en el sistema ni en la carpeta del GTA. samp.dll pide d3dx9_25 y el ENB d3dx9_43.
    public static List<string> Faltan(string sistema, string carpetaGta, bool enb)
    {
        var dlls = new List<string> { "d3dx9_25.dll" };
        if (enb) dlls.Add("d3dx9_43.dll");
        return dlls.Where(d => !File.Exists(Path.Combine(sistema, d)) && (carpetaGta.Length == 0 || !File.Exists(Path.Combine(carpetaGta, d)))).ToList();
    }

    // El GTA es de 32 bits: en un Windows de 64 sus DLL del sistema están en SysWOW64.
    public static string Sistema() { return Environment.GetFolderPath(Environment.SpecialFolder.SystemX86); }

    public static void Instalar(Action<string, int> progreso)
    {
        string carpeta = Path.Combine(Path.GetTempPath(), "AmericaRP-directx"), exe = carpeta + ".exe";
        try
        {
            Actualizador.Bajar(Config.DirectXUrl, exe, "Bajando DirectX 9", progreso);
            if (Actualizador.Sha256(exe) != Config.DirectXSha) throw new InvalidDataException("El instalador de DirectX bajado no es el esperado.");
            progreso("Instalando DirectX 9...", 100);
            if (Directory.Exists(carpeta)) Directory.Delete(carpeta, true);
            Correr(exe, "/Q /T:\"" + carpeta + "\"", false);
            Correr(Path.Combine(carpeta, "DXSETUP.exe"), "/silent", true);
        }
        finally
        {
            try { File.Delete(exe); } catch (Exception) { }
            try { if (Directory.Exists(carpeta)) Directory.Delete(carpeta, true); } catch (Exception) { }
        }
    }

    static void Correr(string exe, string argumentos, bool administrador)
    {
        var psi = new ProcessStartInfo(exe, argumentos) { UseShellExecute = true };
        if (administrador) psi.Verb = "runas";
        try
        {
            using (Process p = Process.Start(psi))
            {
                p.WaitForExit();
                if (p.ExitCode != 0) throw new IOException(Path.GetFileName(exe) + " terminó con el código " + p.ExitCode + ".");
            }
        }
        catch (System.ComponentModel.Win32Exception ex)
        {
            if (ex.NativeErrorCode == 1223) throw new IOException("Hace falta el permiso de administrador para instalarlo.");
            throw;
        }
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
    readonly NotifyIcon bandeja = new NotifyIcon();
    readonly Timer reloj = new Timer(), cuadros = new Timer();
    readonly Stopwatch tiempo = Stopwatch.StartNew();
    readonly Video video = Video.Cargar();
    Point mouse = new Point(-1, -1), arrastre;
    bool arrastrando, consultando, ocupado;

    EstadoServidor server = new EstadoServidor();
    bool serverConsultado;
    string pestana = "inicio", noticias = "Cargando noticias...", estado = "Listo para jugar.", mods = "";
    List<Noticia> listaNoticias = Noticias.Leer("Cargando noticias...");
    int progreso, scroll;
    Actualizador.Revision revision;
    List<string> faltantes = new List<string>(), faltaDx = new List<string>();
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

        bandeja.Text = "AMERICA RP";
        bandeja.Icon = Icon;
        bandeja.MouseClick += delegate { Restaurar(); };
        FormClosed += delegate { bandeja.Visible = false; bandeja.Dispose(); };

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
            BuscarVersion();
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
        faltaDx = Config.DirectXUrl.Length == 0 ? new List<string>() : DirectX.Faltan(DirectX.Sistema(), Carpeta(), EnbActivo());
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
        if (Config.NoticiasUrl.Length == 0) noticias = "Todavía no hay noticias.";
        else
        {
            try { noticias = await Task.Run(() => Web.Texto(Config.NoticiasUrl)); }
            catch (Exception ex) { noticias = "No se pudieron cargar las noticias: " + ex.Message; }
        }
        listaNoticias = Noticias.Leer(noticias);
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

    async void BuscarVersion()
    {
        if (Config.VersionUrl.Length == 0) return;
        KeyValuePair<Version, string> r;
        try { r = Autoactualizacion.Leer(await Task.Run(() => Web.Texto(Config.VersionUrl))); }
        catch (Exception) { return; } // sin internet o sin version.txt: se sigue con este
        if (r.Key <= new Version(Config.Version) || ocupado) return;
        if (!Ajustes.ActualizarSolo && MessageBox.Show(this, "Hay una versión nueva del launcher (" + r.Key + "). Se baja en unos segundos y se vuelve a abrir solo.\n\n¿Actualizar ahora?",
            "AMERICA RP", MessageBoxButtons.YesNo, MessageBoxIcon.Information) != DialogResult.Yes) return;
        if (ocupado) return;
        Ocupar(true);
        string exe = Application.ExecutablePath;
        try { await Task.Run(() => Autoactualizacion.Instalar(exe, r.Key, r.Value, Avisar)); }
        catch (Exception ex)
        {
            Ocupar(false);
            Avisar("No se pudo actualizar el launcher.", 0);
            if (MessageBox.Show(this, "No se pudo actualizar el launcher: " + ex.Message + "\n\n¿Abrir la página para bajarlo a mano?", "AMERICA RP",
                MessageBoxButtons.YesNo, MessageBoxIcon.Warning) == DialogResult.Yes) Abrir(Config.DescargasUrl);
            return;
        }
        Process.Start(exe);
        Application.Exit();
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
        string[] problema = Instalacion.ProblemaCarpeta(carpeta, Instalacion.LugaresMalos());
        if (problema != null && problema[2] == "grave")
        {
            // Avisa y deja seguir: si alguien ya lo instaló todo como administrador, puede jugar igual.
            if (MessageBox.Show(this, problema[1] + "\n\n¿Seguir igual?", "Carpeta del GTA", MessageBoxButtons.YesNo, MessageBoxIcon.Warning) != DialogResult.Yes)
                return false;
        }
        var repartidos = new List<string>();
        if (Config.ManifiestoUrl.Length > 0 && File.Exists(Path.Combine(carpeta, "gta_sa.exe")))
        {
            try { repartidos.AddRange((await Task.Run(() => Actualizador.Aplicar(carpeta, Config.ManifiestoUrl, Avisar))).Entradas.Select(e => e.Value)); }
            catch (Exception ex)
            {
                Avisar("No se pudo actualizar.", 0);
                RevisarMods();
                if (MessageBox.Show(this, ex.Message + "\n\n¿Seguir sin actualizar?", "Actualizaciones", MessageBoxButtons.YesNo, MessageBoxIcon.Warning) != DialogResult.Yes)
                    return false;
            }
            RevisarMods();
        }
        if (Config.CefZipUrl.Length > 0 && File.Exists(Path.Combine(carpeta, "gta_sa.exe")))
        {
            // Sin CEF se juega igual (con los diálogos de siempre): si falla, se avisa y se sigue.
            try { await Task.Run(() => Actualizador.InstalarCef(carpeta, Avisar)); }
            catch (Exception ex) { Avisar("No se pudieron instalar las pantallas del server: " + ex.Message, 0); }
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
        if (Config.ProhibidosUrl.Length > 0 && File.Exists(Path.Combine(carpeta, "gta_sa.exe")))
        {
            if (EnbActivo())
                try { repartidos.AddRange(Actualizador.LeerManifiesto(File.ReadAllText(EnbArchivo())).Select(e => e.Value)); } catch (Exception) { }
            try
            {
                Avisar("Revisando archivos prohibidos...", 0);
                List<string> malos = await Task.Run(() => Prohibidos.Buscar(carpeta, Prohibidos.Leer(Web.Texto(Config.ProhibidosUrl)), repartidos));
                if (malos.Count > 0)
                {
                    string donde = await Task.Run(() => Prohibidos.Sacar(carpeta, malos));
                    MessageBox.Show(this, "Saqué del GTA estos archivos, que no se pueden usar en el server:\n\n" + string.Join("\n", malos.Take(15)) +
                        (malos.Count > 15 ? "\n... y " + (malos.Count - 15) + " más" : "") + "\n\nNo se borraron: quedaron en " + donde,
                        "Archivos prohibidos", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                }
            }
            catch (Exception ex)
            {
                // Sin internet o con un archivo trabado no se frena el juego: el server es el que controla de verdad.
                Avisar("No se pudieron revisar los archivos prohibidos: " + ex.Message, 0);
            }
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
        if (faltaDx.Count > 0 && !await OfrecerDirectX()) return false;
        if (EnbActivo())
        {
            try { if (Instalacion.Poner4Gb(Path.Combine(carpeta, "gta_sa.exe"))) Avisar("Listo el parche de 4 GB para el ENB.", 100); }
            catch (Exception ex) { Avisar("No se pudo poner el parche de 4 GB: " + ex.Message, 0); }
        }
        if (problema != null) Avisar(problema[1], 100);
        if (!gta10) Avisar("Tu gta_sa.exe no parece la versión 1.0. Si el juego se cierra al conectar, instalá la 1.0.", 100);
        return true;
    }

    // Devuelve false si el jugador quiso instalarlo y no se pudo. Si dice que no, se juega igual: puede que lo tenga en otro lado.
    async Task<bool> OfrecerDirectX()
    {
        string sinEso = faltaDx.Contains("d3dx9_25.dll") ? "el SA-MP no abre" : "el ENB no carga";
        if (MessageBox.Show(this, "A tu Windows le falta DirectX 9 (" + string.Join(", ", faltaDx) + "). Sin eso " + sinEso + ".\n\n" +
            "¿Instalarlo ahora? Se baja de Microsoft (96 MB) y Windows te va a pedir permiso de administrador.",
            "DirectX 9", MessageBoxButtons.YesNo, MessageBoxIcon.Warning) != DialogResult.Yes)
        {
            Avisar("Falta DirectX 9: si el juego no abre, instalalo desde MI JUEGO.", 0);
            return true;
        }
        try { await Task.Run(() => DirectX.Instalar(Avisar)); }
        catch (Exception ex)
        {
            Avisar("No se pudo instalar DirectX 9.", 0);
            MessageBox.Show(this, "No se pudo instalar DirectX 9: " + ex.Message, "DirectX 9", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return false;
        }
        RevisarInstalacion();
        if (faltaDx.Count > 0)
        {
            MessageBox.Show(this, "Se instaló DirectX 9 pero sigue faltando " + string.Join(", ", faltaDx) + ".", "DirectX 9", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return false;
        }
        Avisar("DirectX 9 instalado.", 100);
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
            if (Juego.Abierto())
            {
                if (MessageBox.Show(this, "El GTA ya está abierto, aunque puede estar escondido detrás de otras ventanas (por ejemplo, la de elegir la resolución).\n\n" +
                    "¿Cerrarlo y abrir uno nuevo? Si estás jugando, se cierra la partida.", "AMERICA RP", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
                await Task.Run(() => Juego.Cerrar());
                if (Juego.Abierto()) { Avisar("No se pudo cerrar el GTA. Cerralo desde el Administrador de tareas.", 0); return; }
                try { await Task.Run(() => Juego.CerrarCefColgado(Carpeta())); } catch (Exception) { }
            }
            if (!await Preparar()) return;
            string carpeta = Carpeta();
            DateTime inicio = DateTime.Now;
            Juego.DejarPasarAlFrente();
            Process.Start(new ProcessStartInfo(Path.Combine(carpeta, "samp.exe"), Config.Host + ":" + Config.Puerto) { WorkingDirectory = carpeta });
            Avisar("Abriendo el GTA...", 100);
            Vigilar(carpeta, inicio);
        }
        catch (Exception ex) { MessageBox.Show(this, "No se pudo abrir el juego: " + ex.Message, "AMERICA RP", MessageBoxButtons.OK, MessageBoxIcon.Error); }
        finally { Ocupar(false); }
    }

    // Cuando el GTA se cierra vuelve el launcher. Si se cerró de golpe, avisa y deja un informe para soporte.
    async void Vigilar(string carpeta, DateTime inicio)
    {
        IntPtr ventana = IntPtr.Zero;
        try { ventana = await Task.Run(() => Juego.EsperarVentana(carpeta)); } catch (Exception) { }
        if (ventana != IntPtr.Zero) Juego.AlFrente(ventana);
        if (Ajustes.Bandeja)
        {
            bandeja.Visible = true;
            Hide();
        }
        else WindowState = FormWindowState.Minimized;
        Juego.Cierre c;
        try { c = await Task.Run(() => Juego.Esperar(carpeta, inicio)); }
        catch (Exception) { return; }
        if (c == null) { Restaurar(); Avisar("No se vio abrir el GTA. Si no abrió, probá de nuevo.", 0); return; }
        try { await Task.Run(() => Juego.CerrarCefColgado(carpeta)); } catch (Exception) { }
        Restaurar();
        if (c.Bien) { Avisar("Listo para jugar.", 100); return; }
        string informe;
        try { informe = Juego.GuardarInforme(c, carpeta, EnbActivo()); }
        catch (Exception) { informe = null; }
        Avisar("El GTA se cerró de golpe.", 0);
        if (MessageBox.Show(this, "El GTA se cerró de golpe (código " + Juego.CodigoTexto(c.Codigo.Value) + ") después de " + (int)(c.Fin - c.Inicio).TotalMinutes + " min." +
            (informe == null ? "" : "\n\nGuardé un informe para soporte. ¿Abrir la carpeta?"), "AMERICA RP",
            informe == null ? MessageBoxButtons.OK : MessageBoxButtons.YesNo, MessageBoxIcon.Warning) == DialogResult.Yes)
        {
            try { Process.Start("explorer.exe", "/select,\"" + informe + "\""); } catch (Exception) { }
        }
    }

    void Restaurar()
    {
        bandeja.Visible = false;
        Show();
        WindowState = FormWindowState.Normal;
        Activate();
    }

    void CopiarInforme()
    {
        string texto = Soporte.Armar(Revisiones(), Carpeta(), nick.Text.Trim(), EnbActivo(), Soporte.UltimoCierre(Soporte.DirInformes()));
        try { Clipboard.SetText(texto); }
        catch (Exception ex) { MessageBox.Show(this, "No se pudo copiar el informe: " + ex.Message, "Soporte", MessageBoxButtons.OK, MessageBoxIcon.Warning); return; }
        string soporte = Config.Redes.Where(r => r.Key == "Soporte").Select(r => r.Value).FirstOrDefault() ?? "";
        Avisar("Informe copiado. Pegalo con Ctrl+V en el canal de soporte.", 100);
        if (MessageBox.Show(this, "Copié el informe. Pegalo con Ctrl+V en el canal de soporte del Discord y contá qué te pasa." +
            (soporte.Length > 0 ? "\n\n¿Abrir el soporte ahora?" : ""), "Soporte",
            soporte.Length > 0 ? MessageBoxButtons.YesNo : MessageBoxButtons.OK, MessageBoxIcon.Information) == DialogResult.Yes) Abrir(soporte);
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
        else if (pestana == "ajustes") DibujarAjustes(g);
        else DibujarInicio(g);
        DibujarTarjeta(g);
        DibujarPie(g);
    }

    void DibujarArriba(Graphics g)
    {
        Estrella(g, 52, 38, 17, Acento);
        Neon(g, "America RP", Fuentes.Titulo(34f), 76, 20);

        int x = 300;
        foreach (string[] p in new[] { new[] { "inicio", "INICIO" }, new[] { "noticias", "NOTICIAS" }, new[] { "mods", "MODS" }, new[] { "juego", "MI JUEGO" }, new[] { "ajustes", "AJUSTES" } })
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
        Noticia ultima = listaNoticias.FirstOrDefault();
        string primera = ultima == null ? "" : ultima.Titulo.Length > 0 ? ultima.Titulo : ultima.Lineas.FirstOrDefault(l => l.Trim().Length > 0 && !l.Contains("Bienvenido")) ?? "";
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
        Font texto = Fuentes.Texto(12.5f), titulo = Fuentes.Titulo(24f), chica = Fuentes.Negrita(9.5f);
        g.SetClip(area);
        int y = area.Y - scroll;
        foreach (Noticia n in listaNoticias)
        {
            if (n.Etiqueta.Length > 0 || n.Fecha.Length > 0)
            {
                int x = area.X;
                if (n.Etiqueta.Length > 0)
                {
                    string e = n.Etiqueta.ToUpperInvariant();
                    int w = Medir(g, e, chica) + 16;
                    using (var b = new SolidBrush(ColorEtiqueta(n.Etiqueta))) g.FillRectangle(b, x, y, w, 20);
                    Escribir(g, e, chica, Oscuro, x + 8, y + 3);
                    x += w + 10;
                }
                Escribir(g, n.Fecha, chica, Gris, x, y + 3);
                y += 26;
            }
            if (n.Titulo.Length > 0) { Escribir(g, n.Titulo, titulo, Texto, area.X, y); y += 38; }
            foreach (string l in n.Lineas)
            {
                bool punto = l.StartsWith("- ");
                string t = punto ? l.Substring(2) : l;
                int sangria = punto ? 18 : 0;
                int alto = t.Length == 0 ? 10 : (int)g.MeasureString(t, texto, area.Width - sangria).Height;
                if (punto) Punto(g, area.X + 5, y + 11, Acento);
                using (var b = new SolidBrush(Color.FromArgb(225, Texto))) g.DrawString(t, texto, b, new RectangleF(area.X + sangria, y, area.Width - sangria, alto + 4));
                y += alto + 2;
            }
            y += 14;
            using (var p = new Pen(Color.FromArgb(28, 255, 255, 255))) g.DrawLine(p, area.X, y, area.Right, y);
            y += 18;
        }
        g.ResetClip();
        int total = y + scroll - area.Y;
        scroll = Math.Min(scroll, Math.Max(0, total - area.Height));
    }

    Color ColorEtiqueta(string etiqueta)
    {
        string e = etiqueta.ToLowerInvariant();
        if (e.StartsWith("actualiz")) return Acento;
        if (e.StartsWith("arreglo") || e.StartsWith("fix")) return Verde;
        if (e.StartsWith("evento")) return Color.FromArgb(110, 170, 255);
        if (e.StartsWith("aviso")) return Rojo;
        return Gris;
    }

    void DibujarAjustes(Graphics g)
    {
        Rectangle area = Hoja(g, "AJUSTES");
        int y = area.Y;
        FilaAjuste(g, area, ref y, "ESCONDER EL LAUNCHER MIENTRAS JUGÁS", "Se va a la bandeja, al lado del reloj, y vuelve solo cuando cerrás el GTA. Si no, queda minimizado.",
            Ajustes.Bandeja, delegate { Ajustes.Bandeja = !Ajustes.Bandeja; });
        FilaAjuste(g, area, ref y, "ACTUALIZAR EL LAUNCHER SIN PREGUNTAR", "Cuando sale una versión nueva, se instala sola al abrirlo. Si no, te pregunta antes.",
            Ajustes.ActualizarSolo, delegate { Ajustes.ActualizarSolo = !Ajustes.ActualizarSolo; });
        Escribir(g, "INFORMES DE CIERRES DEL GTA", Fuentes.Negrita(13f), Texto, area.X, y + 10);
        Boton(g, new Rectangle(area.Right - 150, y + 4, 150, 34), "ABRIR", false, delegate
        {
            Directory.CreateDirectory(Soporte.DirInformes());
            Abrir(Soporte.DirInformes());
        });
        Escribir(g, "Si el juego se cerró de golpe, acá queda lo que pasó. Soporte te lo puede pedir.", Fuentes.Texto(11f), Gris, area.X, y + 40);
        Escribir(g, "VERSIÓN DEL LAUNCHER " + Config.Version, Fuentes.Negrita(10f), Gris, area.X, area.Bottom - 20);
    }

    void FilaAjuste(Graphics g, Rectangle area, ref int y, string nombre, string detalle, bool activo, Action cambiar)
    {
        Escribir(g, nombre, Fuentes.Negrita(13f), Texto, area.X, y + 10);
        // El botón muestra cómo está y lo cambia al tocarlo: naranja = activado.
        Boton(g, new Rectangle(area.Right - 150, y + 4, 150, 34), activo ? "ACTIVADO" : "DESACTIVADO", activo, cambiar);
        Escribir(g, detalle, Fuentes.Texto(11f), Gris, area.X, y + 40);
        using (var p = new Pen(Color.FromArgb(28, 255, 255, 255))) g.DrawLine(p, area.X, y + 66, area.Right, y + 66);
        y += 76;
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
        Boton(g, new Rectangle(area.X + 216, y + 24, 200, 40), "COPIAR INFORME", false, CopiarInforme);
    }

    // [nombre, valor, ok|ojo|mal|nada]
    List<string[]> Revisiones()
    {
        string carpeta = Carpeta();
        bool hayGta = carpeta.Length > 0 && File.Exists(Path.Combine(carpeta, "gta_sa.exe"));
        bool haySamp = hayGta && File.Exists(Path.Combine(carpeta, "samp.exe")) && File.Exists(Path.Combine(carpeta, "samp.dll"));
        string[] problema = Instalacion.ProblemaCarpeta(carpeta, Instalacion.LugaresMalos());
        int pend = revision == null ? -1 : revision.Pendientes.Count;
        return new List<string[]>
        {
            new[] { "GTA San Andreas 1.0", !hayGta ? "FALTA" : gta10 ? "OK" : "REVISAR", !hayGta ? "mal" : gta10 ? "ok" : "ojo" },
            new[] { "SA-MP 0.3.7", haySamp ? "OK" : "FALTA", haySamp ? "ok" : "mal" },
            new[] { "DirectX 9", faltaDx.Count == 0 ? "OK" : "FALTA", faltaDx.Count == 0 ? "ok" : "mal" },
            new[] { "Lugar de la carpeta", !hayGta ? "-" : problema == null ? "OK" : problema[2] == "grave" ? "MOVERLA" : "REVISAR", !hayGta ? "nada" : problema == null ? "ok" : problema[2] == "grave" ? "mal" : "ojo" },
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
        // En la tarjeta entran cuatro filas: las tres de siempre y, si algo más anda mal, la primera de esas.
        List<string[]> filas = Revisiones();
        string[] otra = filas.Skip(3).FirstOrDefault(f => f[2] == "mal" || f[2] == "ojo");
        filas = filas.Take(3).ToList();
        if (otra != null) filas.Add(otra);
        foreach (string[] fila in filas)
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
        if (args.Length == 1 && args[0] == "--publicar")
        {
            string salida = Path.Combine(Path.GetDirectoryName(Application.ExecutablePath), "launcher", "version.txt");
            Directory.CreateDirectory(Path.GetDirectoryName(salida));
            File.WriteAllText(salida, Autoactualizacion.Linea(Application.ExecutablePath), new UTF8Encoding(false));
            Console.WriteLine("Escrito " + salida + ": " + File.ReadAllText(salida).Trim());
            return 0;
        }
        if (args.Length == 2 && args[0] == "--manifiesto")
        {
            string salida = Path.Combine(Path.GetDirectoryName(Path.GetFullPath(args[1]).TrimEnd(Path.DirectorySeparatorChar)), Actualizador.NombreManifiesto);
            File.WriteAllText(salida, Actualizador.GenerarManifiesto(args[1]), new UTF8Encoding(false));
            Console.WriteLine("Manifiesto escrito en " + salida);
            return 0;
        }
        Autoactualizacion.BorrarViejo(Application.ExecutablePath);
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

        // Zip de CEF: solo cef.asi y cef/, sin el .lib, y nada fuera del GTA.
        carpeta = Path.Combine(Path.GetTempPath(), "amrp-cef-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(carpeta);
        try
        {
            string zip = Path.Combine(carpeta, "cef.zip"), gta = Path.Combine(carpeta, "gta");
            using (ZipArchive z = ZipFile.Open(zip, ZipArchiveMode.Create))
                foreach (string f in new[] { "cef.asi", "cef/client.dll", "cef/locales/es.pak", "cef/libcef.lib", "otro/leeme.txt" })
                    using (var w = new StreamWriter(z.CreateEntry(f).Open())) w.Write(f);
            Actualizador.ExtraerCef(gta, zip);
            Ver(File.Exists(Path.Combine(gta, "cef.asi")) && File.Exists(Path.Combine(gta, "cef", "locales", "es.pak"))
                && !File.Exists(Path.Combine(gta, "cef", "libcef.lib")) && !Directory.Exists(Path.Combine(gta, "otro")), "zip CEF: instala solo cef.asi y cef/");
            string malo = Path.Combine(carpeta, "malo.zip");
            using (ZipArchive z = ZipFile.Open(malo, ZipArchiveMode.Create))
                using (var w = new StreamWriter(z.CreateEntry("cef/../../afuera.txt").Open())) w.Write("x");
            Ver(Tira(() => Actualizador.ExtraerCef(gta, malo)) && !File.Exists(Path.Combine(carpeta, "afuera.txt")), "zip CEF: rechaza rutas de afuera");
        }
        finally { Directory.Delete(carpeta, true); }

        var vid = new List<byte>(Encoding.ASCII.GetBytes("AMRPVID1"));
        vid.AddRange(BitConverter.GetBytes(24));
        vid.AddRange(BitConverter.GetBytes(5)); // dice 5 cuadros pero trae 2 y uno cortado
        for (int i = 0; i < 2; i++) { vid.AddRange(BitConverter.GetBytes(3)); vid.AddRange(new byte[] { 1, 2, 3 }); }
        vid.AddRange(BitConverter.GetBytes(999));
        Ver(Video.Desde(vid.ToArray()).Cuadros == 2, "video: lee solo los cuadros completos");
        Ver(Tira(() => Video.Desde(Encoding.ASCII.GetBytes("cualquier cosa nada"))), "video: rechaza archivo que no es video");

        string sha64 = new string('a', 64);
        var ver = Autoactualizacion.Leer("1.2.0 " + sha64 + "\r\n");
        Ver(ver.Key == new Version(1, 2, 0) && ver.Value == sha64 && new Version("1.10.0") > new Version("1.9.0"), "version.txt: se lee y compara");
        Ver(Tira(() => Autoactualizacion.Leer("1.2.0")) && Tira(() => Autoactualizacion.Leer("uno " + sha64)) && Tira(() => Autoactualizacion.Leer("1.2.0 " + sha64.ToUpperInvariant())), "version.txt: rechaza formatos raros");
        carpeta = Path.Combine(Path.GetTempPath(), "amrp-exe-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(carpeta);
        try
        {
            string exe = Path.Combine(carpeta, "AmericaRP.exe"), nuevo = exe + ".nuevo";
            File.WriteAllText(exe, "viejo");
            File.WriteAllText(exe + ".viejo", "de antes");
            File.WriteAllText(nuevo, "nuevo");
            Autoactualizacion.Reemplazar(exe, nuevo);
            Ver(File.ReadAllText(exe) == "nuevo" && File.ReadAllText(exe + ".viejo") == "viejo" && !File.Exists(nuevo), "launcher: el nuevo toma el lugar del viejo");
            bool fallo = false;
            try { Autoactualizacion.Reemplazar(exe, Path.Combine(carpeta, "no-existe.exe")); } catch (Exception) { fallo = true; }
            Ver(fallo && File.ReadAllText(exe) == "nuevo", "launcher: si falla, queda el que estaba");
            Autoactualizacion.BorrarViejo(exe);
            Ver(!File.Exists(exe + ".viejo"), "launcher: borra el .viejo al arrancar");

            string sis = Path.Combine(carpeta, "sys"), gtaDx = Path.Combine(carpeta, "gta");
            Directory.CreateDirectory(sis);
            Directory.CreateDirectory(gtaDx);
            Ver(DirectX.Faltan(sis, gtaDx, true).Count == 2 && DirectX.Faltan(sis, gtaDx, false).SequenceEqual(new[] { "d3dx9_25.dll" }), "DirectX: detecta las que faltan");
            File.WriteAllText(Path.Combine(sis, "d3dx9_25.dll"), "x");
            File.WriteAllText(Path.Combine(gtaDx, "d3dx9_43.dll"), "x");
            Ver(DirectX.Faltan(sis, gtaDx, true).Count == 0 && DirectX.Faltan(sis, "", true).SequenceEqual(new[] { "d3dx9_43.dll" }), "DirectX: vale en el sistema o en la carpeta del GTA");
        }
        finally { Directory.Delete(carpeta, true); }

        carpeta = Path.Combine(Path.GetTempPath(), "amrp-e2-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(carpeta);
        string cacheAntes = Actualizador.CacheRuta;
        try
        {
            Actualizador.CacheRuta = Path.Combine(carpeta, "huellas.txt");
            Actualizador.OlvidarHuellas();
            string f = Path.Combine(carpeta, "a.img");
            File.WriteAllText(f, "abc");
            DateTime fecha = new DateTime(2026, 1, 1, 0, 0, 0, DateTimeKind.Utc);
            File.SetLastWriteTimeUtc(f, fecha);
            string h1 = Actualizador.HuellaRapida(f);
            File.WriteAllText(f, "xyz"); // mismo tamaño y misma fecha: no lo vuelve a leer
            File.SetLastWriteTimeUtc(f, fecha);
            Actualizador.OlvidarHuellas(); // y lo recuerda aunque se cierre el launcher
            Ver(h1 == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad" && Actualizador.HuellaRapida(f) == h1, "huellas: no relee un archivo sin cambios");
            File.SetLastWriteTimeUtc(f, fecha.AddSeconds(1));
            Ver(Actualizador.HuellaRapida(f) == "3608bca1e44ea6c4d268eb6db02260269892c0b42b86bbf1e77a6fa16c3c9282", "huellas: si cambió la fecha lo vuelve a leer");
            File.WriteAllText(Actualizador.CacheRuta, "basura sin tabulador\n\t\n");
            Actualizador.OlvidarHuellas();
            Ver(Actualizador.HuellaRapida(f) == "3608bca1e44ea6c4d268eb6db02260269892c0b42b86bbf1e77a6fa16c3c9282", "huellas: un archivo de memoria roto no molesta");

            // Parche de 4 GB sobre un .exe mínimo: pone la marca una vez, guarda copia y no toca otra cosa.
            byte[] exe = new byte[0x200];
            exe[0] = (byte)'M'; exe[1] = (byte)'Z';
            BitConverter.GetBytes(0x80).CopyTo(exe, 0x3C);
            exe[0x80] = (byte)'P'; exe[0x81] = (byte)'E';
            exe[0x80 + 22] = 0x02;
            string gtaExe = Path.Combine(carpeta, "gta_sa.exe");
            File.WriteAllBytes(gtaExe, exe);
            bool puso = Instalacion.Poner4Gb(gtaExe);
            byte[] despues = File.ReadAllBytes(gtaExe);
            Ver(puso && despues[0x80 + 22] == 0x22 && despues.Length == exe.Length && File.ReadAllBytes(gtaExe + ".sin4gb").SequenceEqual(exe), "4 GB: pone la marca y guarda la copia");
            Ver(!Instalacion.Poner4Gb(gtaExe) && File.ReadAllBytes(gtaExe + ".sin4gb").SequenceEqual(exe), "4 GB: la segunda vez no hace nada");
            File.WriteAllText(gtaExe, "no soy un exe");
            Ver(Tira(() => Instalacion.Poner4Gb(gtaExe)), "4 GB: rechaza un archivo que no es .exe");

            // american.gxt
            string g = Path.Combine(carpeta, "gta");
            Directory.CreateDirectory(Path.Combine(g, "text"));
            foreach (string n in new[] { "gta_sa.exe", "samp.exe", "samp.dll" }) File.WriteAllText(Path.Combine(g, n), "x");
            Ver(Instalacion.Faltantes(g).Count == 1 && Instalacion.Faltantes(g)[0].Contains("american.gxt") && !Instalacion.Faltantes(g)[0].Contains("SA-MP"), "falta american.gxt");
            File.WriteAllText(Path.Combine(g, "text", "american.gxt"), "x");
            Ver(Instalacion.Faltantes(g).Count == 0, "con american.gxt no falta nada");

            // Lugar de la carpeta
            string pf = Path.Combine(carpeta, "Program Files"), od = Path.Combine(carpeta, "OneDrive");
            var lugares = new List<string[]> { new[] { "", "vacío", "" }, new[] { pf, "pf", "grave" }, new[] { od, "od", "" } };
            Ver(Instalacion.ProblemaCarpeta(Path.Combine(pf, "Rockstar", "GTA"), lugares)[1] == "pf" && Instalacion.ProblemaCarpeta(Path.Combine(od, "GTA"), lugares)[2] == ""
                && Instalacion.ProblemaCarpeta(Path.Combine(carpeta, "Program Files (x86)", "GTA"), lugares) == null && Instalacion.ProblemaCarpeta(Path.Combine(carpeta, "Juegos"), lugares) == null, "lugar de la carpeta");

            // Informe de cierre
            string chat = Path.Combine(carpeta, "chatlog.txt");
            File.WriteAllLines(chat, Enumerable.Range(1, 40).Select(i => "linea " + i));
            string[] ult = Juego.Ultimas(chat, 30);
            Ver(ult.Length == 30 && ult[0] == "linea 11" && ult[29] == "linea 40" && Juego.Ultimas(Path.Combine(carpeta, "no.txt"), 5).Length == 0, "informe: últimas líneas del chat");
            var cierre = new Juego.Cierre { Codigo = unchecked((int)0xC0000005), Inicio = new DateTime(2026, 11, 4, 10, 0, 0), Fin = new DateTime(2026, 11, 4, 10, 12, 30) };
            string inf = Juego.Informe(cierre, "D:\\GTA", true, ult);
            Ver(!cierre.Bien && inf.Contains("0xC0000005 (acceso") && inf.Contains("12 min") && inf.Contains("ENB activo: sí") && inf.Contains("linea 40"), "informe: código, tiempo y log");
            Ver(new Juego.Cierre { Codigo = 0 }.Bien && new Juego.Cierre().Bien && Juego.CodigoTexto(1).StartsWith("0x00000001 (lo cerraron"), "cierre normal o sin código no avisa");
        }
        finally
        {
            Actualizador.CacheRuta = cacheAntes;
            Actualizador.OlvidarHuellas();
            Directory.Delete(carpeta, true);
        }

        var nots = Noticias.Leer("## 2026-11-04 | Actualización | Teléfono nuevo\r\nAhora el teléfono se abre con /telefono.\n- Se cierra con Esc\n- Anda el chat\n\n## 2026-11-01 | Evento | Carrera | con premio\nTexto\n## Sin partes\n");
        Ver(nots.Count == 3 && nots[0].Fecha == "2026-11-04" && nots[0].Etiqueta == "Actualización" && nots[0].Titulo == "Teléfono nuevo"
            && nots[0].Lineas.Count == 3 && nots[0].Lineas[1] == "- Se cierra con Esc" && nots[1].Titulo == "Carrera | con premio" && nots[2].Titulo == "Sin partes" && nots[2].Etiqueta == "", "noticias con formato");
        var viejas = Noticias.Leer("Hola\n\nchau");
        Ver(viejas.Count == 1 && viejas[0].Titulo == "" && viejas[0].Lineas.SequenceEqual(new[] { "Hola", "", "chau" }), "noticias en texto plano siguen andando");

        carpeta = Path.Combine(Path.GetTempPath(), "amrp-e3-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(carpeta);
        string ajustesAntes = Ajustes.Ruta;
        try
        {
            Ajustes.Ruta = Path.Combine(carpeta, "ajustes.txt");
            Ver(Ajustes.Bandeja && !Ajustes.ActualizarSolo, "ajustes: valores de fábrica");
            Ajustes.Bandeja = false;
            Ajustes.ActualizarSolo = true;
            Ver(!Ajustes.Bandeja && Ajustes.ActualizarSolo && File.ReadAllLines(Ajustes.Ruta).Length == 2, "ajustes: se guardan");
            File.WriteAllText(Ajustes.Ruta, "basura\n=x\nbandeja=si\n");
            Ver(Ajustes.Bandeja && !Ajustes.ActualizarSolo, "ajustes: un archivo raro no rompe");

            Ver(Soporte.UltimoCierre(Path.Combine(carpeta, "no-existe")) == "", "soporte: sin informes");
            File.WriteAllText(Path.Combine(carpeta, "cierre-20261101-100000.txt"), "AMERICA RP\nCódigo de salida: viejo\n\nchat");
            File.WriteAllText(Path.Combine(carpeta, "cierre-20261104-100000.txt"), "AMERICA RP: el GTA se cerró de golpe\nCódigo de salida: 0xC0000005\nTiempo jugado: 3 min\n\nÚltimas líneas\nhola");
            string uc = Soporte.UltimoCierre(carpeta);
            Ver(uc == "Código de salida: 0xC0000005\nTiempo jugado: 3 min", "soporte: toma el último cierre sin el chat");
            string inf = Soporte.Armar(new List<string[]> { new[] { "DirectX 9", "OK", "ok" } }, "D:\\GTA", "Juan_Perez", false, uc);
            Ver(inf.Contains("Launcher: " + Config.Version) && inf.Contains("DirectX 9: OK") && inf.Contains("Nick: Juan_Perez") && inf.Contains("0xC0000005") && !inf.Contains("hola"), "soporte: arma el informe");
        }
        finally
        {
            Ajustes.Ruta = ajustesAntes;
            Directory.Delete(carpeta, true);
        }

        carpeta = Path.Combine(Path.GetTempPath(), "amrp-p-" + Guid.NewGuid().ToString("N"));
        try
        {
            Directory.CreateDirectory(Path.Combine(carpeta, "cleo"));
            Directory.CreateDirectory(Path.Combine(carpeta, "_prohibidos", "viejo", "cleo"));
            File.WriteAllText(Path.Combine(carpeta, "cleo", "Aimbot_v2.cs"), "x");
            File.WriteAllText(Path.Combine(carpeta, "cleo", "fps.cs"), "x");
            File.WriteAllText(Path.Combine(carpeta, "cleo", "renombrado.cs"), "abc");
            File.WriteAllText(Path.Combine(carpeta, "s0beit.asi"), "x");
            File.WriteAllText(Path.Combine(carpeta, "samp.dll"), "x");
            File.WriteAllText(Path.Combine(carpeta, "salida_limpia.asi"), "x");
            File.WriteAllText(Path.Combine(carpeta, "_prohibidos", "viejo", "s0beit.asi"), "x");
            var lista = Prohibidos.Leer("# comentario\r\ncleo/*aimbot*   # trampa\n*.asi\nsamp.dll\n../fuera\nBA7816BF8F01CFEA414140DE5DAE2223B00361A396177A9CB410FF61F20015AD\n");
            Ver(lista.Rutas.Count == 3 && lista.Huellas.Count == 1, "prohibidos: lee la lista");
            List<string> malos = Prohibidos.Buscar(carpeta, lista, new[] { "salida_limpia.asi" });
            Ver(malos.SequenceEqual(new[] { "cleo/Aimbot_v2.cs", "cleo/renombrado.cs", "s0beit.asi" }), "prohibidos: encuentra por nombre y huella, y cuida lo del server (" + string.Join(",", malos) + ")");
            string donde = Prohibidos.Sacar(carpeta, malos);
            Ver(!File.Exists(Path.Combine(carpeta, "s0beit.asi")) && File.Exists(Path.Combine(donde, "cleo", "Aimbot_v2.cs")) && File.Exists(Path.Combine(carpeta, "cleo", "fps.cs"))
                && Prohibidos.Buscar(carpeta, lista, new[] { "salida_limpia.asi" }).Count == 0, "prohibidos: los mueve sin borrar");
        }
        finally { Directory.Delete(carpeta, true); }

        Ver(Instalacion.NickValido.IsMatch("Juan_Perez") && !Instalacion.NickValido.IsMatch("ab") && !Instalacion.NickValido.IsMatch("con espacio"), "nick");
        Console.WriteLine(fallas == 0 ? "Todo bien." : fallas + " falla(s).");
        return fallas == 0 ? 0 : 1;
    }
}
