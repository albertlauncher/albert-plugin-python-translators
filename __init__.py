# -*- coding: utf-8 -*-
# Copyright (c) 2024 Manuel Schneider

"""
Translates text using the python package [translators](https://pypi.org/project/translators/).
"""

import os
import re
from locale import getlocale
from pathlib import Path
from time import sleep

os.environ["translators_default_region"] = "EN"
import translators as ts
from albert import *

md_iid = "5.0"
md_version = "2.2.2"
md_name = "Translator"
md_description = "Translate text using online translators"
md_license = "MIT"
md_url = "https://github.com/albertlauncher/albert-plugin-python-translators"
md_authors = ["@ManuelSchneid3r"]
md_lib_dependencies = ["translators"]
md_maintainers = ["@ManuelSchneid3r"]


def make_icon():
    return Icon.image(Path(__file__).parent / "google_translate.png")


def make_error_icon():
    return Icon.composed(make_icon(), Icon.grapheme("⚠️"))


class Plugin(PluginInstance, GeneratorQueryHandler):

    def __init__(self):
        PluginInstance.__init__(self)
        GeneratorQueryHandler.__init__(self)

        self._translator = self.readConfig('translator', str)
        if self._translator is None:
            self._translator = 'google'

        self.language = 'en'
        self.languages = dict()
        self.update_languages()

    def update_languages(self):
        try:
            self.languages = ts.get_languages(self.translator)
        except Exception as e:
            self.languages = dict()
            warning(str(e))
        self.language = self.language_from_locale()
        if self.language not in self.languages:
            self.language = 'en'

    @staticmethod
    def language_from_locale():
        language_code = getlocale()[0]  # https://docs.python.org/3/library/locale.html#locale.getlocale
        if language_code:  # https://docs.python.org/3/library/locale.html#locale-name
            return re.split(r'[._-]', language_code, maxsplit=1)[0].lower()
        else:  # 'C' locale
            return 'en'

    @property
    def translator(self):
        return self._translator

    @translator.setter
    def translator(self, value):
        self._translator = value
        self.writeConfig('translator', value)
        self.update_languages()

    def defaultTrigger(self):
        return 'tr '

    def configWidget(self):
        return [
            {
                'type': 'label',
                'text': __doc__.strip(),
                'widget_properties': {'textFormat': 'Qt::MarkdownText'}
            },
            {
                'type': 'combobox',
                'property': 'translator',
                'label': 'Translator',
                'items': ts.translators_pool
            }
        ]

    def synopsis(self, query):
        return "[[from] to] text"

    def items(self, context):
        if not self.languages:
            yield [
                StandardItem(
                    id=self.id(),
                    text="Plugin initialization failed",
                    subtext="Activate to try again",
                    icon_factory=make_error_icon,
                    actions=[Action(id="init", text="Initialize plugin", callable=self.update_languages)]
                )
            ]
            return

        query = context.query.strip()
        if not query:
            return

        for _ in range(50):
            sleep(0.01)
            if not context.isValid:
                return

        if len(splits := query.split(maxsplit=2)) == 3 \
                and splits[0] in self.languages and splits[1] in self.languages.get(splits[0], []):
            src, dst, text = splits
        elif len(splits := query.split(maxsplit=1)) == 2 \
                and splits[0] in self.languages.get(self.language, []):
            src, dst, text = 'auto', splits[0], splits[1]
        else:
            src, dst, text = 'auto', self.language, query

        try:
            translation = ts.translate_text(query_text=text,
                                            translator=self.translator,
                                            from_language=src,
                                            to_language=dst,
                                            timeout=5)

            actions = []
            if havePasteSupport():
                actions.append(Action("paste", "Copy & Paste", lambda t=translation: setClipboardTextAndPaste(t)))
            actions.append(Action("copy", "Copy to clipboard", lambda t=translation: setClipboardText(t)))

            yield [
                StandardItem(
                    id=self.id(),
                    text=translation,
                    subtext=f"{src.upper()} > {dst.upper()}",
                    icon_factory=make_icon,
                    actions=actions
                )
            ]

        except Exception as e:
            warning(str(e))
            yield [
                StandardItem(
                    id=self.id(),
                    text="Error",
                    subtext=str(e),
                    icon_factory=make_icon
                )
            ]
