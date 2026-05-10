# Bóveda local cifrada

Esta carpeta guarda memoria operativa que puede ser sensible o semisensible.

Regla principal: July conserva solo el índice mental y el puntero. El contenido delicado vive aquí cifrado con DPAPI de Windows para el usuario actual.

## Comandos

Desde la raíz de `Mente_unificada`:

```powershell
.\scripts\secure-memory.ps1 -Action list
```

Sellar una nota desde un archivo temporal:

```powershell
.\scripts\secure-memory.ps1 -Action seal -Key "indalo-padel/mcp-tooling" -PlaintextPath .\ruta\nota.txt
```

Sellar una nota escribiendo el texto en prompt oculto:

```powershell
.\scripts\secure-memory.ps1 -Action seal -Key "indalo-padel/mcp-tooling"
```

Abrir una nota:

```powershell
.\scripts\secure-memory.ps1 -Action open -Key "indalo-padel/mcp-tooling"
```

## Seguridad

- No se guardan claves maestras en el repo.
- El cifrado usa `windows-dpapi-current-user`; solo el usuario Windows actual puede descifrarlo en esta máquina.
- `context/secure/vault/*.dpapi.json` está ignorado por Git.
- `context/secure/index.json` solo debe contener metadatos no secretos: clave lógica, ruta local, tipo de protección y fecha.
- No guardar valores crudos de `.env`, tokens, service-role keys o passwords en July.
