# -*- coding: utf-8 -*-

from branca.element import Figure, JavascriptLink, MacroElement

from folium.utilities import parse_options

from jinja2 import Template


class BrowserPrint(MacroElement):
    """ Add a browser print widget on the map.

    Parameters
    ----------
    position: str, default 'topright'
        Location of the widget.
    print_modes: list, default 'landscape'

    See https://github.com/Igor-Vladyka/leaflet.browser.print for more information.

    """
    _template = Template("""
        {% macro script(this, kwargs) %}
            var {{ this.get_name() }} = new L.control.browserPrint(
                {{ this.options|tojson }});
            {{this._parent.get_name()}}.addControl({{this.get_name()}});

        {% endmacro %}
        """)  # noqa

    def __init__(self, position='topleft', print_modes=['landscape'], **kwargs):

        super(BrowserPrint, self).__init__()
        self._name = 'BrowserPrint'

        self.options = parse_options(
            position=position,
            print_modes=print_modes,
            **kwargs
        )

    def render(self, **kwargs):
        super(BrowserPrint, self).render()

        figure = self.get_root()
        assert isinstance(figure, Figure), ('You cannot render this Element '
                                            'if it is not in a Figure.')

        figure.header.add_child(
            JavascriptLink('https://www.usbr.gov/uc/water/hydrodata/assets/leaflet/js/leaflet.browser.print.min.js')
        )
            