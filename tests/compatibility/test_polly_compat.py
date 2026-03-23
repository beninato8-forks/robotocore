"""Compatibility tests for Amazon Polly."""

import uuid

import pytest

from tests.compatibility.conftest import make_client


@pytest.fixture
def polly_client():
    return make_client("polly")


@pytest.fixture
def s3_bucket():
    """Create an S3 bucket for Polly output, yield its name, then delete it."""
    s3 = make_client("s3")
    bucket_name = f"polly-compat-{uuid.uuid4().hex[:12]}"
    s3.create_bucket(Bucket=bucket_name)
    yield bucket_name
    try:
        # Delete all objects first
        objects = s3.list_objects_v2(Bucket=bucket_name).get("Contents", [])
        for obj in objects:
            s3.delete_object(Bucket=bucket_name, Key=obj["Key"])
        s3.delete_bucket(Bucket=bucket_name)
    except Exception as exc:
        import logging

        logging.debug("s3_bucket cleanup failed: %s", exc)


@pytest.fixture
def lexicon_name(polly_client):
    """Create a lexicon, yield its name, then delete it."""
    name = f"compat{uuid.uuid4().hex[:8]}"
    polly_client.put_lexicon(
        Name=name,
        Content=(
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<lexicon version="1.0"'
            ' xmlns="http://www.w3.org/2005/01/pronunciation-lexicon"'
            ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
            ' xsi:schemaLocation="http://www.w3.org/2005/01/pronunciation-lexicon'
            ' http://www.w3.org/2005/01/pronunciation-lexicon"'
            ' alphabet="ipa" xml:lang="en-US">'
            "<lexeme><grapheme>W3C</grapheme>"
            "<alias>World Wide Web Consortium</alias></lexeme>"
            "</lexicon>"
        ),
    )
    yield name
    try:
        polly_client.delete_lexicon(Name=name)
    except Exception:
        pass  # best-effort cleanup


class TestDescribeVoices:
    def test_returns_voices_list(self, polly_client):
        resp = polly_client.describe_voices()
        voices = resp["Voices"]
        assert isinstance(voices, list)
        assert len(voices) > 0

    def test_voice_has_expected_fields(self, polly_client):
        resp = polly_client.describe_voices()
        voice = resp["Voices"][0]
        assert "Id" in voice
        assert "Name" in voice
        assert "LanguageCode" in voice
        assert "Gender" in voice

    def test_filter_by_language(self, polly_client):
        resp = polly_client.describe_voices(LanguageCode="en-US")
        voices = resp["Voices"]
        assert len(voices) > 0
        for v in voices:
            assert v["LanguageCode"] == "en-US"


class TestSynthesizeSpeech:
    def test_mp3_output(self, polly_client):
        resp = polly_client.synthesize_speech(
            OutputFormat="mp3",
            Text="Hello world",
            VoiceId="Joanna",
        )
        assert resp["ContentType"] == "audio/mpeg"
        data = resp["AudioStream"].read()
        assert len(data) > 0

    def test_different_voice(self, polly_client):
        resp = polly_client.synthesize_speech(
            OutputFormat="mp3",
            Text="Testing",
            VoiceId="Matthew",
        )
        assert resp["ContentType"] == "audio/mpeg"
        data = resp["AudioStream"].read()
        assert len(data) > 0


class TestLexicons:
    def test_put_and_list_lexicon(self, polly_client, lexicon_name):
        resp = polly_client.list_lexicons()
        names = [lex["Name"] for lex in resp["Lexicons"]]
        assert lexicon_name in names

    def test_get_lexicon(self, polly_client, lexicon_name):
        resp = polly_client.get_lexicon(Name=lexicon_name)
        assert resp["Lexicon"]["Name"] == lexicon_name
        assert "Content" in resp["Lexicon"]
        assert "LexiconAttributes" in resp

    def test_delete_lexicon(self, polly_client):
        name = f"compat{uuid.uuid4().hex[:8]}"
        polly_client.put_lexicon(
            Name=name,
            Content=(
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<lexicon version="1.0"'
                ' xmlns="http://www.w3.org/2005/01/pronunciation-lexicon"'
                ' alphabet="ipa" xml:lang="en-US">'
                "<lexeme><grapheme>test</grapheme>"
                "<alias>testing</alias></lexeme>"
                "</lexicon>"
            ),
        )
        polly_client.delete_lexicon(Name=name)
        resp = polly_client.list_lexicons()
        names = [lex["Name"] for lex in resp["Lexicons"]]
        assert name not in names

    def test_list_lexicons_empty(self, polly_client):
        resp = polly_client.list_lexicons()
        assert "Lexicons" in resp
        assert isinstance(resp["Lexicons"], list)


class TestSpeechSynthesisTasks:
    """Tests for async speech synthesis task management."""

    def test_start_and_get_speech_synthesis_task(self, polly_client, s3_bucket):
        """StartSpeechSynthesisTask creates a task and GetSpeechSynthesisTask retrieves it."""
        resp = polly_client.start_speech_synthesis_task(
            Engine="standard",
            OutputFormat="mp3",
            OutputS3BucketName=s3_bucket,
            Text="Hello world",
            VoiceId="Joanna",
        )
        task = resp["SynthesisTask"]
        assert "TaskId" in task
        assert task["TaskStatus"] in ("scheduled", "inProgress", "completed", "failed")
        assert "OutputUri" in task
        assert s3_bucket in task["OutputUri"]

        task_id = task["TaskId"]
        get_resp = polly_client.get_speech_synthesis_task(TaskId=task_id)
        get_task = get_resp["SynthesisTask"]
        assert get_task["TaskId"] == task_id
        assert get_task["TaskStatus"] in ("scheduled", "inProgress", "completed", "failed")
        assert get_task["VoiceId"] == "Joanna"
        assert get_task["OutputFormat"] == "mp3"

    def test_list_speech_synthesis_tasks(self, polly_client, s3_bucket):
        """ListSpeechSynthesisTasks returns tasks that were started."""
        polly_client.start_speech_synthesis_task(
            OutputFormat="mp3",
            OutputS3BucketName=s3_bucket,
            Text="First task",
            VoiceId="Joanna",
        )
        polly_client.start_speech_synthesis_task(
            OutputFormat="mp3",
            OutputS3BucketName=s3_bucket,
            Text="Second task",
            VoiceId="Matthew",
        )

        resp = polly_client.list_speech_synthesis_tasks()
        assert "SynthesisTasks" in resp
        tasks = resp["SynthesisTasks"]
        assert len(tasks) >= 2
        for task in tasks:
            assert "TaskId" in task
            assert "TaskStatus" in task

    def test_get_speech_synthesis_task_not_found(self, polly_client):
        """GetSpeechSynthesisTask raises SynthesisTaskNotFoundException for unknown TaskId."""
        from botocore.exceptions import ClientError

        with pytest.raises(ClientError) as exc:
            polly_client.get_speech_synthesis_task(TaskId="nonexistent-task-id-xyz")
        assert exc.value.response["Error"]["Code"] == "SynthesisTaskNotFoundException"


class TestPollyErrors:
    """Tests for Polly error handling."""

    def test_get_lexicon_nonexistent(self, polly_client):
        """GetLexicon for nonexistent lexicon raises LexiconNotFoundException."""
        from botocore.exceptions import ClientError

        with pytest.raises(ClientError) as exc:
            polly_client.get_lexicon(Name="nonexistent-lexicon-xyz")
        assert exc.value.response["Error"]["Code"] == "LexiconNotFoundException"

    def test_delete_lexicon_nonexistent(self, polly_client):
        """DeleteLexicon for nonexistent lexicon raises LexiconNotFoundException."""
        from botocore.exceptions import ClientError

        with pytest.raises(ClientError) as exc:
            polly_client.delete_lexicon(Name="nonexistent-lexicon-xyz")
        assert exc.value.response["Error"]["Code"] == "LexiconNotFoundException"
