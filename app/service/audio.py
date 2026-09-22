from random import choice
from uuid import UUID

from celery import chain
from fastapi import UploadFile
from pydub import AudioSegment
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.schemas.audio import CensorOptions, SubtitleOptions
from app.database.models import Audio, User
from app.object_storage import storage
from app.service.user import UserService
from app.worker.tasks import (
    detect_profanity_task,
    render_audio_task,
    transcribe_audio_task,
)


class AudioService:
    def __init__(self, session: AsyncSession, user_service: UserService):
        self.session = session
        self.user_service = user_service

    async def get_audio(self, id: UUID) -> Audio | None:
        return await self.session.get(Audio, id)

    async def get_subtitle(
        self, id: UUID, user: User, options: SubtitleOptions
    ) -> str | None:
        audio = await self.session.get(Audio, id)
        if audio is None or audio.user_id != user.id:
            return None

        if not audio.transcription:
            raise ValueError("Audio transcription is not ready")

        return self._build_srt(audio.transcription, options)

    async def add_audio(
        self,
        file: UploadFile,
        user: User,
        options: CensorOptions | None = None,
    ) -> Audio:
        duration = round(AudioSegment.from_file(file.file).duration_seconds)

        required_credits = duration * 3
        await self.user_service.deduct_credits(user, required_credits)

        # Save the uploaded file to disk
        storage.upload_file(
            file.file,
            key=file.filename,
            content_type=file.content_type,
        )

        # Add audio record to database
        audio = Audio(
            name=file.filename.split(".")[0],
            duration=duration,
            file_path=file.filename,
            credits_reserved=required_credits,
            user_id=user.id,
            user_list=options.user_list if options else None,
            use_beep=options.use_beep if options else False,
            sound_effect_id=options.sound_effect_id if options else None,
        )
        self.session.add(audio)
        await self.session.commit()
        await self.session.refresh(audio)

        # Trigger the background task to censor the audio
        chain(
            transcribe_audio_task.si(str(audio.id)),
            detect_profanity_task.si(str(audio.id)),
            render_audio_task.si(str(audio.id)),
        ).apply_async()

        return audio

    async def update_audio(
        self,
        id: UUID,
        user: User,
        options: CensorOptions,
    ) -> Audio | None:
        audio = await self.session.get(Audio, id)
        if audio is None or audio.user_id != user.id:
            return None

        user_list_changed = audio.user_list != options.user_list

        required_credits = audio.duration * (2 if user_list_changed else 1)
        await self.user_service.deduct_credits(user, required_credits)
        audio.credits_reserved += required_credits

        audio.user_list = options.user_list
        audio.use_beep = options.use_beep
        audio.sound_effect_id = options.sound_effect_id

        self.session.add(audio)
        await self.session.commit()
        await self.session.refresh(audio)

        if user_list_changed:
            chain(
                detect_profanity_task.si(str(audio.id)),
                render_audio_task.si(str(audio.id)),
            ).apply_async()
        else:
            render_audio_task.delay(str(audio.id))

        return audio

    @staticmethod
    def _mask_word(word: str, options: SubtitleOptions) -> str:
        visible_chars = max(0, options.visible_chars)
        visible_count = 0
        masked_word: list[str] = []
        mask_symbols = options.symbol or "*"

        for char in word:
            if not char.isalnum():
                masked_word.append(char)
                continue

            if visible_count < visible_chars:
                masked_word.append(char)
                visible_count += 1
                continue

            masked_word.append(choice(mask_symbols))

        return "".join(masked_word)

    @staticmethod
    def _format_srt_timestamp(seconds: float) -> str:
        total_milliseconds = max(0, round(seconds * 1000))
        hours, remainder = divmod(total_milliseconds, 3_600_000)
        minutes, remainder = divmod(remainder, 60_000)
        secs, milliseconds = divmod(remainder, 1000)
        return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"

    def _build_srt(self, transcription: list[dict], options: SubtitleOptions) -> str:
        subtitle_blocks: list[str] = []
        cue_words: list[str] = []
        cue_start: float | None = None
        cue_end: float | None = None

        for segment in transcription:
            word = str(segment.get("word", "")).strip()
            if not word:
                continue

            if segment.get("flagged", False):
                word = self._mask_word(word, options)

            start = float(segment.get("start", 0.0))
            end = float(segment.get("end", start))

            if cue_start is None:
                cue_start = start

            cue_words.append(word)
            cue_end = max(end, start)

            if word.endswith((".", "!", "?")) or len(cue_words) >= 12:
                subtitle_blocks.append(
                    self._render_srt_block(
                        index=len(subtitle_blocks) + 1,
                        start=cue_start,
                        end=cue_end,
                        text=" ".join(cue_words),
                    )
                )
                cue_words = []
                cue_start = None
                cue_end = None

        if cue_words and cue_start is not None and cue_end is not None:
            subtitle_blocks.append(
                self._render_srt_block(
                    index=len(subtitle_blocks) + 1,
                    start=cue_start,
                    end=cue_end,
                    text=" ".join(cue_words),
                )
            )

        return "\n\n".join(subtitle_blocks)

    def _render_srt_block(self, index: int, start: float, end: float, text: str) -> str:
        if end <= start:
            end = start + 0.001

        return "\n".join(
            [
                str(index),
                f"{self._format_srt_timestamp(start)} --> {self._format_srt_timestamp(end)}",
                text,
            ]
        )
