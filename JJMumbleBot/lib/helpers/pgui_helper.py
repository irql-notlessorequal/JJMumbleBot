class PGUIHelper:

    @staticmethod
    def font_mod(text, params=None):
        if params is None:
            params = []
        txt = f'<font '
        for i, item in enumerate(params):
            txt += f'{item} '
        txt += f'>{text}</font>'
        return txt

    @staticmethod
    def color(color):
        return f'color="{color}"'

    @staticmethod
    def face(font):
        return f'face="{font}"'

    @staticmethod
    def bold(text):
        return f'<b>{text}</b>'

    @staticmethod
    def italicize(text):
        return f'<i>{text}</i>'

    @staticmethod
    def underline(text):
        return f'<u>{text}</u>'

    @staticmethod
    def content(text, tt="data", tc='white', tf='Calibri', ta="center"):
        txt_color = PGUIHelper.color(tc)
        txt_face = PGUIHelper.face(tf)
        if tt == 'data':
            content = f'<td align="{ta}">{PGUIHelper.font_mod(text, params=[txt_color, txt_face])}</td>'
            return content
        if tt == 'header':
            content = f'<th align="{ta}">{PGUIHelper.font_mod(text, params=[txt_color, txt_face])}</th>'
            return content
        return None

    @staticmethod
    def img_content(text):
        content = f'<td align="left">{text}</td>'
        return content
