#include <direct.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>

static int ensure_dir(const char *path) {
    if (_mkdir(path) == 0) {
        return 0;
    }
    if (errno == EEXIST) {
        return 0;
    }
    fprintf(stderr, "nodelect: no se pudo crear directorio '%s'\n", path);
    return 1;
}

static int write_shim(const char *out_dir, const char *name, const char *content) {
    char path[1024];
    FILE *f;

    snprintf(path, sizeof(path), "%s\\%s", out_dir, name);
    f = fopen(path, "wb");
    if (!f) {
        fprintf(stderr, "nodelect: no se pudo crear '%s'\n", path);
        return 1;
    }

    if (fwrite(content, 1, strlen(content), f) != strlen(content)) {
        fclose(f);
        fprintf(stderr, "nodelect: no se pudo escribir '%s'\n", path);
        return 1;
    }

    fclose(f);
    return 0;
}

int main(int argc, char **argv) {
    const char *out_dir = "..\\dist\\shims";
    const char *files[] = {"node.cmd", "npm.cmd", "npx.cmd"};
    const size_t file_count = sizeof(files) / sizeof(files[0]);
    const char *script =
        "@echo off\r\n"
        "setlocal EnableExtensions EnableDelayedExpansion\r\n"
        "\r\n"
        "if \"%%LOCALAPPDATA%%\"==\"\" (\r\n"
        "  >&2 echo nodelect: LOCALAPPDATA no definido\r\n"
        "  exit /b 1\r\n"
        ")\r\n"
        "\r\n"
        "set \"VERSION_PATH=%%LOCALAPPDATA%%\\nodelect\\nodejs\\current\"\r\n"
        "if not exist \"%%VERSION_PATH%%\" (\r\n"
        "  >&2 echo nodelect: sin version activa. Ejecuta 'nodelect use ^<version^>'\r\n"
        "  exit /b 1\r\n"
        ")\r\n"
        "\r\n"
        "set /p \"VERSION=\"<\"%%VERSION_PATH%%\"\r\n"
        "if errorlevel 1 (\r\n"
        "  >&2 echo nodelect: no se pudo leer el archivo de version\r\n"
        "  exit /b 1\r\n"
        ")\r\n"
        "if \"%%VERSION%%\"==\"\" (\r\n"
        "  >&2 echo nodelect: no hay version de node activa. Ejecuta 'nodelect use ^<version^>'\r\n"
        "  exit /b 1\r\n"
        ")\r\n"
        "\r\n"
        "set \"BINARY=%%~n0\"\r\n"
        "for %%%%L in (A=a B=b C=c D=d E=e F=f G=g H=h I=i J=j K=k L=l M=m N=n O=o P=p Q=q R=r S=s T=t U=u V=v W=w X=x Y=y Z=z) do (\r\n"
        "  set \"BINARY=!BINARY:%%%%L!\"\r\n"
        ")\r\n"
        "if \"!BINARY!\"==\"\" (\r\n"
        "  >&2 echo nodelect: no se pudo determinar el nombre del binario\r\n"
        "  exit /b 1\r\n"
        ")\r\n"
        "\r\n"
        "set \"TARGET_EXE=%%LOCALAPPDATA%%\\nodelect\\nodejs\\versions\\%%VERSION%%\\!BINARY!.exe\"\r\n"
        "set \"TARGET_CMD=%%LOCALAPPDATA%%\\nodelect\\nodejs\\versions\\%%VERSION%%\\!BINARY!.cmd\"\r\n"
        "\r\n"
        "setlocal DisableDelayedExpansion\r\n"
        "if exist \"%%TARGET_EXE%%\" goto :run_exe\r\n"
        "if not exist \"%%TARGET_CMD%%\" (\r\n"
        "  >&2 echo nodelect: no se encuentra '%%~n0' en version %%VERSION%%\r\n"
        "  exit /b 1\r\n"
        ")\r\n"
        "\r\n"
        "cmd.exe /d /c \"\"%%TARGET_CMD%%\" %%*\"\r\n"
        "set \"EXIT_CODE=%%ERRORLEVEL%%\"\r\n"
        "exit /b %%EXIT_CODE%%\r\n"
        "\r\n"
        ":run_exe\r\n"
        "\"%%TARGET_EXE%%\" %%*\r\n"
        "set \"EXIT_CODE=%%ERRORLEVEL%%\"\r\n"
        "exit /b %%EXIT_CODE%%\r\n";

    size_t i;

    if (argc > 1 && argv[1] && argv[1][0]) {
        out_dir = argv[1];
    }

    if (strcmp(out_dir, "..\\dist\\shims") == 0) {
        if (ensure_dir("..\\dist") != 0) {
            return 1;
        }
    }

    if (ensure_dir(out_dir) != 0) {
        return 1;
    }

    for (i = 0; i < file_count; i++) {
        if (write_shim(out_dir, files[i], script) != 0) {
            return 1;
        }
    }
    return 0;
}