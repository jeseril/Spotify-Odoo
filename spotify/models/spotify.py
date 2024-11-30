from odoo import models, fields, api
import requests,logging

_logger = logging.getLogger(__name__)

class SpotifyIntegration(models.Model):
    _name = 'spotify.integration'
    _description = 'Spotify Integration'

    client_id = fields.Char(string='Client ID', required=True)
    client_secret = fields.Char(string='Client Secret', required=True)
    access_token = fields.Char(string='Access Token')
    token_type = fields.Char(string='Token Type')
    state = fields.Char(string='State')

    user_id = fields.Char(string='User ID', readonly=True)
    playlist_ids = fields.One2many('spotify.playlist', 'integration_id', string='Playlists')
    expires_in = fields.Integer(string='Token Expiry Time')  # Tiempo de expiración del token

    @api.model
    def create(self, values):
        existing_record = self.search([('client_id', '=', values.get('client_id'))], limit=1)
        if existing_record:
            # Si el registro ya existe, actualizamos los valores y luego obtenemos el ID del usuario
            existing_record.write(values)
            existing_record.fetch_user_id()
            return existing_record
        else:
            # Si no existe, creamos un nuevo registro
            new_record = super(SpotifyIntegration, self).create(values)
            new_record.fetch_user_id()  # Aseguramos que el método se ejecute también cuando creamos un nuevo registro
            return new_record

    @api.model
    def get_integration(self):
        return self.search([], limit=1)

    def authenticate(self):
        # Lógica para obtener el token de acceso
        auth_url = 'http://localhost:8069/spotify/auth'
        return {
            'type': 'ir.actions.act_url',
            'url': auth_url,
            'target': 'new',  # Abrir en una nueva ventana
        }

    def fetch_user_id(self):
        try:
            url = "https://api.spotify.com/v1/me"
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                user_info = response.json()
                # El ID del usuario está directamente en el campo 'id'
                self.user_id = user_info.get('id')
                _logger.info(f"User ID: {self.user_id}")
            else:
                # Imprimir el contenido completo de la respuesta de error
                error_info = response.json()  # La respuesta es un JSON
                _logger.error(f"Error {response.status_code}: {error_info}")
                raise ValueError(f"Failed to fetch user info: {error_info}")

        except requests.exceptions.RequestException as e:
            _logger.error(f"Error de conexión al intentar obtener el ID del usuario: {str(e)}")
        except Exception as e:
            _logger.error(f"Error inesperado al intentar obtener el ID del usuario: {str(e)}")

    def fetch_playlist(self):
        self.fetch_user_id()
        try:
            base_url = f"https://api.spotify.com/v1/users/{self.user_id}/playlists"
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            limit = 50
            offset = 0
            playlists = []

            # Paginación
            while True:
                url = f"{base_url}?limit={limit}&offset={offset}"
                response = requests.get(url, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    current_playlists = data.get('items', [])
                    playlists.extend(current_playlists)

                    if not data.get('next'):
                        break

                    offset += limit
                else:
                    raise ValueError(f"Failed to fetch playlists: {response.json()}")

            # Creamos o actualizamos las playlists
            for playlist in playlists:
                if playlist:  # Validar que no sea None
                    try:
                        existing_playlist = self.env['spotify.playlist'].search([
                            ('spotify_id', '=', playlist.get('id'))
                        ], limit=1)

                        if existing_playlist:
                            _logger.info(
                                f"La playlist '{playlist.get('name', 'Sin nombre')}' ya existe. Actualizando canciones.")
                            existing_playlist.fetch_tracks()  # Llamamos a fetch_tracks para actualizar las canciones
                        else:
                            # Crear la playlist si no existe
                            _logger.info(
                                f"La playlist '{playlist.get('name', 'Sin nombre')}' no existe. Creando nueva playlist.")
                            self.env['spotify.playlist'].create({
                                'name': playlist.get('name', 'Sin nombre'),
                                'spotify_id': playlist.get('id', 'Sin ID'),
                                'integration_id': self.id
                            })
                            # Ahora que se ha creado, actualizamos las canciones
                            new_playlist = self.env['spotify.playlist'].search([
                                ('spotify_id', '=', playlist.get('id'))
                            ], limit=1)
                            if new_playlist:
                                new_playlist.fetch_tracks()  # Llamamos a fetch_tracks para crear las canciones en la nueva playlist

                    except Exception as e:
                        _logger.error(f"Error al procesar playlist {playlist.get('name', 'Sin nombre')}: {str(e)}")

        except requests.exceptions.RequestException as e:
            _logger.error(f"Error de conexión al intentar obtener playlists: {str(e)}")
            raise
        except Exception as e:
            _logger.error(f"Error inesperado en fetch_playlist: {str(e)}")
            raise

class SpotifyPlaylist(models.Model):
    _name = 'spotify.playlist'
    _description = 'Spotify Playlist'

    name = fields.Char(string='Playlist Name', required=True)
    spotify_id = fields.Char(string='Spotify ID', required=True)
    integration_id = fields.Many2one('spotify.integration', string='Integration')
    track_ids = fields.One2many('spotify.track', 'playlist_id', string='Tracks')

    @api.model
    def create(self, values):
        # Crear la playlist
        playlist = super(SpotifyPlaylist, self).create(values)
        # Llamar a fetch_tracks para obtener las canciones de la nueva playlist
        try:
            playlist.fetch_tracks()
        except Exception as e:
            _logger.error(f"Error al obtener las canciones para la playlist {playlist.name}: {str(e)}")

        return playlist

    def fetch_tracks(self):
        integration = self.integration_id
        if not integration.access_token:
            raise ValueError("Access token is missing. Please authenticate first.")

        url = f"https://api.spotify.com/v1/playlists/{self.spotify_id}/tracks"
        headers = {
            'Authorization': f"Bearer {integration.access_token}"
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            tracks = response.json().get('items', [])

            # Recopilar los IDs de las canciones que vienen de la API
            api_track_ids = {item.get('track', {}).get('id') for item in tracks}

            # Buscar todos los tracks de la playlist en Odoo
            existing_tracks = self.env['spotify.track'].search([
                ('playlist_id', '=', self.id)
            ])

            # Eliminar los tracks que ya no están en la respuesta de la API
            for existing_track in existing_tracks:
                if existing_track.spotify_id not in api_track_ids:
                    _logger.info(f"Eliminando la canción '{existing_track.name}' porque ya no está en la playlist.")
                    existing_track.unlink()  # Eliminar el track de Odoo

            # Crear o actualizar las canciones que están en la respuesta de la API
            for item in tracks:
                track = item.get('track', {})
                track_name = track.get('name')
                track_id = track.get('id')
                track_artists = ', '.join([artist.get('name') for artist in track.get('artists', [])])

                # Verificar si la canción ya existe en la base de datos
                existing_track = self.env['spotify.track'].search([
                    ('spotify_id', '=', track_id),
                    ('playlist_id', '=', self.id)
                ], limit=1)

                if not existing_track:
                    # Si no existe, crear un nuevo registro de track en Odoo
                    self.env['spotify.track'].create({
                        'name': track_name,
                        'spotify_id': track_id,
                        'artists': track_artists,
                        'playlist_id': self.id,
                    })
                else:
                    _logger.info(f"La canción '{track_name}' ya existe en la playlist. No se creará de nuevo.")
        else:
            raise ValueError(f"Failed to fetch tracks: {response.json()}")

class SpotifyTrack(models.Model):
    _name = 'spotify.track'
    _description = 'Spotify Track'

    name = fields.Char(string='Track Name', required=True)
    artists = fields.Char(string='Artist', required=True)
    spotify_id = fields.Char(string='Spotify ID', required=True)
    playlist_id = fields.Many2one('spotify.playlist', string='Playlist')