import string,json,urllib,random,logging
from odoo import http
from odoo.http import request
from werkzeug.utils import redirect  # Import redirect from werkzeug

_logger = logging.getLogger(__name__)

class SpotifyController(http.Controller):

    @http.route('/spotify/auth', type='http', auth="public", website=True)
    def spotify_auth(self, **kwargs):
        spotify_integration = request.env['spotify.integration'].search([], limit=1)

        if not spotify_integration:
            return "Spotify integration credentials not found."

        client_id = spotify_integration.client_id
        redirect_uri = 'http://localhost:8069/spotify/callback'
        state = self._generate_random_string(16)
        request.session['spotify_state'] = state

        scope = 'user-read-private user-read-email playlist-read-private playlist-read-collaborative'

        auth_url = f"https://accounts.spotify.com/authorize?" \
                   f"response_type=token&client_id={client_id}&scope={urllib.parse.quote(scope)}" \
                   f"&redirect_uri={urllib.parse.quote(redirect_uri)}&state={state}"

        return redirect(auth_url)  # Use redirect from werkzeug

    def _generate_random_string(self, length=16):
        """Generate a random string of the specified length."""
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))


class SpotifyCallbackController(http.Controller):
    @http.route('/spotify/callback', type='http', auth='public', csrf=False, website=True)
    def spotify_callback(self, **kwargs):
        # Redirigir a una página donde JavaScript pueda capturar el token
        return request.render('spotify.spotify_callback_page', {})

class SpotifyController(http.Controller):

    @http.route('/spotify/save_token', type='json', auth='public', methods=['POST'])
    def save_token(self, **kwargs):
        # Obtener el cuerpo de la solicitud usando httprequest.get_data()
        data = request.httprequest.get_data(as_text=True)

        try:
            # Convertir los datos de la solicitud a JSON
            data = json.loads(data)
            _logger.info(f"Recibido token: {data}")  # Log para ver los parámetros recibidos
        except Exception as e:
            _logger.error(f"Error al convertir el cuerpo a JSON: {e}")
            return {"status": "error", "message": "Error al procesar la solicitud"}

        access_token = data.get('access_token')
        token_type = data.get('token_type')
        expires_in = data.get('expires_in')
        state = data.get('state')

        # Asegúrate de que se recibieron todos los parámetros
        if not all([access_token, token_type, expires_in, state]):
            return {"status": "error", "message": "Faltan parámetros en la solicitud"}

        # Guarda el token (puedes guardarlo en el modelo adecuado)
        spotify_integration = request.env['spotify.integration'].search([], limit=1)
        if spotify_integration:
            spotify_integration.write({
                'access_token': access_token,
                'token_type': token_type,
                'expires_in': expires_in,
                'state': state,
            })
            return {"status": "success", "message": "Token guardado con éxito"}
        else:
            return {"status": "error", "message": "No se encontró la integración de Spotify"}





