{
    'name': 'Spotify',
    'version': '1.0',
    'category': 'Connector',
    'summary': 'Integration with Spotify API',
    'description': """
        This module integrates Odoo with Spotify API to:
        - Authenticate using client ID and secret.
        - Fetch and list user playlists.
        - Show tracks in selected playlists.
    """,
    'author': 'Jesus Rincon',
    'website': 'https://www.linkedin.com/in/jesussebastian/',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/spotify_views.xml',
        'views/callback.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}