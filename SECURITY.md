# 🛡️ Política de Seguridad & Gobernanza de Acceso al Repositorio

Este documento define la arquitectura de seguridad, control de acceso y protección de integridad implementada en el repositorio **GeoDataIQ / Coordenadas_demo**.

---

## 1. Modelo de Autorización y Permisos de GitHub

A pesar de que este repositorio es **PÚBLICO** (permitiendo que reclutadores, evaluadores y la comunidad exploren el código y la arquitectura libremente), **ÚNICAMENTE el propietario del repositorio (`@AndresSantiagoJimenez`) tiene permisos de escritura (`git push`)**.

### Niveles de Acceso:
| Rol | Quién | Permiso de Lectura (`Clone / Pull`) | Permiso de Escritura Directa (`Push`) | Capacidad de Merge a `main` |
|---|---|:---:|:---:|:---:|
| **Propietario (Owner)** | `@AndresSantiagoJimenez` | ✅ Sí | ✅ Sí (bajo reglas) | ✅ Exclusivo |
| **Público / Terceros** | Cualquier usuario de GitHub | ✅ Sí | ❌ Bloqueado | ❌ Bloqueado |

> [!IMPORTANT]
> Los usuarios externos **no pueden hacer `git push`** a tus ramas ni modificar tu repositorio. Si alguien desea proponer una mejora, debe forzear un `fork` en su propia cuenta y abrir un `Pull Request`, el cual solo puede ser aprobado y fusionado por ti tras superar los Quality Gates de CI/CD.

---

## 2. Configuración Recomendada de Branch Protection Rules (Paso a Paso)

Para blindar la rama `main` contra modificaciones no autorizadas, commits accidentales o sobreescritura de historial (`force push`), sigue estos pasos en la interfaz de GitHub:

1. Ve a tu repositorio en GitHub: `https://github.com/AndresSantiagoJimenez/Coordenadas_demo`
2. Haz clic en la pestaña **Settings** (Configuración) en la parte superior.
3. En el menú lateral izquierdo, haz clic en **Branches** (Ramas).
4. En la sección **Branch protection rules**, haz clic en **Add branch ruleset** o **Add rule**:
   - **Branch name pattern**: escribe `main`.
5. Activa las siguientes casillas de verificación esenciales:
   - ✅ **Require a pull request before merging**: Exige que todo cambio pase por un PR y no por push directo descontrolado.
     - *(Opcional)* Desmarca "Require approvals" si vas a hacer merges tú mismo sin requerir una segunda persona.
   - ✅ **Require status checks to pass before merging**: Exige que el pipeline de GitHub Actions (`CI - Integración Continua & Quality Gate`) pase en verde antes de que se pueda integrar cualquier commit.
     - Marca `test-and-security` como required check.
   - ✅ **Require conversation resolution before merging**: Todos los comentarios deben quedar resueltos.
   - ✅ **Require signed commits**: Solo permite commits firmados criptográficamente con tu llave GPG o SSH, imposibilitando que alguien suplante tu autoría.
   - ✅ **Do not allow bypassing the above settings**: Aplica las reglas a todos los usuarios, asegurando disciplina de ingeniería de datos.
   - 🚫 **NO activar / Denegar**: `Allow force pushes` (evita que un `git push --force` borre el historial).
   - 🚫 **NO activar / Denegar**: `Allow deletions` (impide que la rama principal sea eliminada).
6. Haz clic en **Save changes**.

---

## 3. GitHub Secret Scanning & Push Protection

Para garantizar que jamás se filtren credenciales, tokens de API o datos privados al repositorio público:

1. En **Settings** > **Code security and analysis**:
   - Activa **Secret scanning**: GitHub monitoreará automáticamente cada commit en busca de tokens y contraseñas.
   - Activa **Push protection**: GitHub **rechazará de inmediato en la terminal** cualquier intento de `git push` que contenga un token o credencial sensible antes de que llegue a los servidores públicos.
   - Activa **Dependabot alerts** y **Dependabot security updates**: Parches automáticos para dependencias con vulnerabilidades.

---

## 4. Archivo CODEOWNERS

El archivo [`.github/CODEOWNERS`](.github/CODEOWNERS) asigna formalmente la propiedad de todo el código:

```text
* @AndresSantiagoJimenez
```

Esto garantiza que GitHub reconozca a `@AndresSantiagoJimenez` como el único revisor autorizado para cualquier cambio propuesto en cualquier ruta del proyecto.

---

## 5. Prevención de Fuga de Datos Masivos y Privacidad

- **Filtrado en `.gitignore`**: Los datos crudos pesados de más de 3 GB (`Data/DANE/`, `Data/features_mgn2025/`, etc.) están excluidos del control de versiones para evitar errores de tamaño de GitHub y mantener la privacidad de datos.
- **Pre-commit Hooks**: El archivo [`.pre-commit-config.yaml`](.pre-commit-config.yaml) restringe localmente la inclusión de archivos de más de 5 MB y escanea con `bandit` antes de confirmar cualquier commit.
- **Cumplimiento de Privacidad**: Los datos procesados se agregan a nivel de manzana censal de acuerdo con la **Ley 1581 de 2012** (Habeas Data) y el **Principio de Secreto Estadístico** (Ley 79 de 1993 y Ley 2335 de 2023 DANE). No se procesa ningún dato de identificación personal (PII).

---

## 6. Reporte de Vulnerabilidades

Si detectas alguna brecha de seguridad o inquietud técnica, por favor comunícate directamente con el mantenedor del proyecto:
- **Mantenedor**: Andrés Santiago Jiménez
- **GitHub**: [@AndresSantiagoJimenez](https://github.com/AndresSantiagoJimenez)
