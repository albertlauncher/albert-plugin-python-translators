# -*- coding: utf-8 -*-
# Copyright (c) 2024 Manuel Schneider

"""
Translates text using the python package [translators](https://pypi.org/project/translators/).
"""

from locale import getdefaultlocale
from pathlib import Path
from time import sleep

from albert import *
import translators as ts

md_iid = "5.0"
md_version = "2.2.2"
md_name = "Translator"
md_description = "Translate text using online translators"
md_license = "MIT"
md_url = "https://github.com/albertlauncher/albert-plugin-python-translators"
md_authors = ["@ManuelSchneid3r"]
md_lib_dependencies = ["translators"]
md_maintainers = ["@ManuelSchneid3r"]


class Plugin(PluginInstance, GeneratorQueryHandler):

    def __init__(self):
        PluginInstance.__init__(self)
        GeneratorQueryHandler.__init__(self)

        self._translator = self.readConfig('translator', str)
        if self._translator is None:
            self._translator = 'google'

        self._lang = self.readConfig('lang', str)
        if self._lang is None:
            self._lang = getdefaultlocale()[0][0:2]

        try:
            languages = ts.get_languages(self.translator)
            self.src_languages = set(languages.keys())
            self.dst_languages = set(languages[self.lang])
        except Exception as e:
            warning(str(e))

    @staticmethod
    def makeIcon():
        return Icon.image(Path(__file__).parent / "google_translate.png")

    @property
    def translator(self):
        return self._translator

    @translator.setter
    def translator(self, value):
        self._translator = value
        self.writeConfig('translator', value)
        languages = ts.get_languages(self.translator)
        self.src_languages = set(languages.keys())
        self.dst_languages = set(languages[self.lang])

    @property
    def lang(self):
        return self._lang

    @lang.setter
    def lang(self, value):
        self._lang = value
        self.writeConfig('lang', value)

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
            },
            {
                'type': 'lineedit',
                'property': 'lang',
                'label': 'Default language',
            }
        ]

    def synopsis(self, s):
        return "[[from] to] text"

    def items(self, ctx):
        query = ctx.query.strip()
        if not query:
            return []

        for _ in range(50):
            sleep(0.01)
            if not ctx.isValid:
                return []

        if len(splits := query.split(maxsplit=2)) == 3 \
                and splits[0] in self.src_languages and splits[1] in self.dst_languages:
            src, dst, text = splits
        elif len(splits := query.split(maxsplit=1)) == 2 and splits[0] in self.src_languages:
            src, dst, text = 'auto', splits[0], splits[1]
        else:
            src, dst, text = 'auto', self.lang, query

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
                    icon_factory=Plugin.makeIcon,
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
                    icon_factory=Plugin.makeIcon
                )
            ]
