# Integración Spotify y Odoo

Sigue estos pasos para integrar Spotify con Odoo:

1. **Instalar el módulo Spotify** en tu instancia de Odoo.
2. Ve a **Ajustes > Técnico > Spotify Integration**.
3. Ingresa las credenciales:
   - **Client ID** y **Client Secret**
4. Guarda la configuración y da click en el botón Authenticate.
5. Haz clic en **Fetch Playlists** para cargar todas las playlists de tu cuenta de Spotify.

* Si se añaden o eliminan canciones de una playlist, al hacer clic nuevamente en Fetch Playlists, la lista se actualizará automáticamente.

Para más detalles, consulta el tutorial en video:  
[Ver video en YouTube](https://youtu.be/mmKcQRNgKng)

- **Redirect URI**:  
  `http://localhost:8069/spotify/callback`

