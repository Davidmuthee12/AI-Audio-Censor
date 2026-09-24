import asyncio

from httpx import AsyncClient

_audio_file_path = "tests/sample.wav"


async def test_audio_censoring(client: AsyncClient, patch_cloud_services):
    with open(_audio_file_path, "rb") as audio_file:
        print("(🧪) uploading audio file")
        submit_response = await client.post(
            "/audio/",
            files={"file": ("sample.wav", audio_file, "audio/wav")},
        )

    assert submit_response.is_success
    submit_payload = submit_response.json()
    assert "id" in submit_payload

    audio_id = submit_payload["id"]
    status = submit_payload["status"]

    for _ in range(10):
        print("(🧪) reading audio")

        read_response = await client.get(f"/audio/{audio_id}")
        assert read_response.is_success

        read_payload = read_response.json()
        status = read_payload["status"]
        assert status != "failed"

        if status == "completed":
            break

        await asyncio.sleep(1)

    assert status == "completed"

    download_response = await client.get(f"/audio/{audio_id}/download")
    assert download_response.is_success

    download_payload = download_response.json()
    assert "file_url" in download_payload

    print("(🧪) audio file download URL:", download_payload["file_url"])
