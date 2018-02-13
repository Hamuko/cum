from unittest import mock
import cumtest


class TestCLIChapters(cumtest.CumCLITest):
    def test_chapters(self):
        FOLLOW = {'url': ('https://manga.madokami.al/Manga/D/DA/DATE/Date'
                          '%20a%20Live'),
                  'alias': 'date-a-live', 'name': 'Date A Live', }
        GROUP = ['Village Idiot']
        CHAPTERS = [
            {'chapter': '1', 'title': 'Date 1 - Spirit'},
            {'chapter': '2', 'title': 'Date 2 - Method'},
            {'chapter': '3', 'title': 'Date 3 - Training'},
            {'chapter': '4', 'title': 'Date 4 - Encounter'},
            {'chapter': '5', 'title': 'Date 5 - Tohka'},
            {'chapter': '6', 'title': 'Date 6 - Battle Commence! [End]'}
        ]
        MESSAGES = [
            'f  chapter  title [group]',
            '         1  Date 1 - Spirit [Village Idiot]',
            'i        2  Date 2 - Method [Village Idiot]',
            'n        3  Date 3 - Training [Village Idiot]',
            'n        4  Date 4 - Encounter [Village Idiot]',
            'n        5  Date 5 - Tohka [Village Idiot]',
            'n        6  Date 6 - Battle Commence! [End] [Village Idiot]'
        ]

        series = self.create_mock_series(**FOLLOW)
        for chapter_info in CHAPTERS:
            chapter_info['alias'] = FOLLOW['alias']
            chapter_info['url'] = chapter_info['chapter']
            chapter_info['name'] = FOLLOW['name']
            chapter_info['groups'] = GROUP
            chapter = self.create_mock_chapter(**chapter_info)
            series.chapters.append(chapter)
        series.follow()

        chapter_1 = (self.db.session.query(self.db.Chapter)
                                    .filter_by(chapter='1').one())
        chapter_2 = (self.db.session.query(self.db.Chapter)
                                    .filter_by(chapter='2').one())
        chapter_1.downloaded = 1
        chapter_2.downloaded = -1
        self.db.session.commit()

        result = self.invoke('chapters', 'date-a-live')
        self.assertEqual(result.exit_code, 0)
        for message in MESSAGES:
            self.assertIn(message, result.output)

    def test_chapters_invalid_alias(self):
        MESSAGE = 'Could not find alias "invalidalias"'

        result = self.invoke('chapters', 'invalidalias')
        self.assertEqual(result.exit_code, 1)
        self.assertIn(MESSAGE, result.output)
