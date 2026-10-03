import asyncio


async def run(*args: str):
    p = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    _, err = await p.communicate()
    if p.returncode != 0:
        raise RuntimeError(err.decode(errors="ignore")[-600:])


async def ffmpeg(*args: str):
    await run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args)
