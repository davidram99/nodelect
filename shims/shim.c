#include <windows.h>
#include <stdio.h>
#include <string.h>

static void trim_newline(char *s) {
    s[strcspn(s, "\r\n")] = 0;
}

int main(void) {
    /* 1. Directorio LOCALAPPDATA */
    char *localappdata = getenv("LOCALAPPDATA");
    if (!localappdata) {
        fprintf(stderr, "nodelect: LOCALAPPDATA no definido\n");
        return 1;
    }

    /* 2. Leer version activa */
    char version_path[MAX_PATH];
    snprintf(version_path, MAX_PATH, "%s\\nodelect\\nodejs\\current", localappdata);

    FILE *f = fopen(version_path, "r");
    if (!f) {
        fprintf(stderr, "nodelect: sin version activa. Ejecuta 'nodelect use <version>'\n");
        return 1;
    }
    char version[64] = {0};

    /* C1: Verificar retorno de fgets */
    if (!fgets(version, sizeof(version), f)) {
        fclose(f);
        fprintf(stderr, "nodelect: no se pudo leer el archivo de version\n");
        return 1;
    }
    fclose(f);
    trim_newline(version);

    /* C2: Validar que la version no este vacia */
    if (version[0] == '\0') {
        fprintf(stderr, "nodelect: no hay version de node activa. Ejecuta 'nodelect use <version>'\n");
        return 1;
    }

    /* 3. Nombre propio del shim (node / npm / npx) */
    char own_path[MAX_PATH];
    GetModuleFileNameA(NULL, own_path, MAX_PATH);
    char *base = strrchr(own_path, '\\');
    base = base ? base + 1 : own_path;
    char binary[64];
    strncpy(binary, base, 63);
    binary[63] = 0;
    char *dot = strrchr(binary, '.');
    if (dot) *dot = 0;  /* "node.exe" -> "node" */

    /* C3: Normalizar binary a minusculas */
    _strlwr(binary); /* "Node" -> "node", "NPM" -> "npm" */

    /* C2: Validar que binary no este vacio */
    if (binary[0] == '\0') {
        fprintf(stderr, "nodelect: no se pudo determinar el nombre del binario\n");
        return 1;
    }

    /* 4. Ruta al binario real: intentar .exe, caer a .cmd via cmd.exe */
    char target_exe[MAX_PATH];
    char target_cmd[MAX_PATH];
    snprintf(target_exe, MAX_PATH,
             "%s\\nodelect\\nodejs\\versions\\%s\\%s.exe", localappdata, version, binary);
    snprintf(target_cmd, MAX_PATH,
             "%s\\nodelect\\nodejs\\versions\\%s\\%s.cmd", localappdata, version, binary);

    int use_cmd_wrapper = 0;
    if (GetFileAttributesA(target_exe) == INVALID_FILE_ATTRIBUTES) {
        if (GetFileAttributesA(target_cmd) == INVALID_FILE_ATTRIBUTES) {
            fprintf(stderr, "nodelect: no se encuentra '%s' en version %s\n",
                    binary, version);
            return 1;
        }
        use_cmd_wrapper = 1;
    }

    /* 5. Reconstruir command line */
    char cmdline[32768];
    char *orig = GetCommandLineA();

    /* Saltar el primer token (ruta del shim) */
    char *args = orig;
    if (*args == '"') {
        args++;
        while (*args && *args != '"') args++;
        if (*args) args++;
    } else {
        while (*args && *args != ' ' && *args != '\t') args++;
    }

    /* C4: Saltar espacios tras el primer token y garantizar separador */
    while (*args == ' ' || *args == '\t') args++;

    if (use_cmd_wrapper) {
        snprintf(cmdline, sizeof(cmdline),
                 "cmd.exe /d /c \"%s\"%s%s",
                 target_cmd,
                 *args ? " " : "",
                 args);
    } else {
        snprintf(cmdline, sizeof(cmdline),
                 "\"%s\"%s%s",
                 target_exe,
                 *args ? " " : "",
                 args);
    }

    /* 6. Lanzar y propagar exit code */

    /* C5: Heredar unicamente stdin, stdout y stderr */
    STARTUPINFOA si = {0};
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESTDHANDLES;
    si.hStdInput  = GetStdHandle(STD_INPUT_HANDLE);
    si.hStdOutput = GetStdHandle(STD_OUTPUT_HANDLE);
    si.hStdError  = GetStdHandle(STD_ERROR_HANDLE);

    PROCESS_INFORMATION pi = {0};

    BOOL ok = use_cmd_wrapper
        ? CreateProcessA(NULL,       cmdline, NULL, NULL, TRUE, 0, NULL, NULL, &si, &pi)
        : CreateProcessA(target_exe, cmdline, NULL, NULL, TRUE, 0, NULL, NULL, &si, &pi);

    if (!ok) {
        fprintf(stderr, "nodelect: error al lanzar proceso (codigo %lu)\n",
                GetLastError());
        return 1;
    }

    WaitForSingleObject(pi.hProcess, INFINITE);
    DWORD exit_code = 1;

    /* C6: Manejo explicito de error en GetExitCodeProcess */
    if (!GetExitCodeProcess(pi.hProcess, &exit_code)) {
        fprintf(stderr, "nodelect: no se pudo obtener el codigo de salida (codigo %lu)\n",
                GetLastError());
    }
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);

    return (int)exit_code;
}