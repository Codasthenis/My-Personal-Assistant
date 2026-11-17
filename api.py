import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Header, HTTPException
from telegram import Update

from main import BOT_APPLICATIONS
from loader import WEBHOOK_SECRETS, logger
import asyncio
from telegram.error import NetworkError



@asynccontextmanager
async def lifespan(api_app: FastAPI):
    initialized = []
    started = []

    try:
        for bot_id, bot_app in BOT_APPLICATIONS.items():
            for attempt in range(1, 4):
                try:
                    await bot_app.initialize()
                    initialized.append(bot_app)

                    await bot_app.start()
                    started.append(bot_app)

                    logger.info(
                        f"{bot_id} started successfully."
                    )
                    break

                except NetworkError as error:
                    logger.warning(
                        f"{bot_id}: Network error "
                        f"(attempt {attempt}/3): {error}"
                    )

                    if attempt == 3:
                        raise

                    await asyncio.sleep(3)

        base_url = "https://v2wzd3.bot-keep.xyz"

        for bot_id, bot_app in BOT_APPLICATIONS.items():
            allowed_updates = (
                ["message", "callback_query", "channel_post"]
                if bot_id == "bot1"
                else ["channel_post"]
            )

            success = await bot_app.bot.set_webhook(
                url=f"{base_url}/webhook/{bot_id}",
                secret_token=WEBHOOK_SECRETS[bot_id],
                allowed_updates=allowed_updates,
                drop_pending_updates=False,
            )

            if not success:
                raise RuntimeError(
                    f"Could not register webhook for {bot_id}"
                )

            logger.info(f"Webhook registered for {bot_id}.")

        logger.info("All six bots are ready.")

        yield

    finally:
        for bot_app in reversed(started):
            await bot_app.stop()

        for bot_app in reversed(initialized):
            await bot_app.shutdown()

        logger.info("All bots have been shut down.")



app = FastAPI(
    title="Telegram Bot API",
    description="Webhook server for six Telegram bots",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Telegram Bot API",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/webhook/{bot_id}")
async def receive_webhook(
    bot_id: str,
    request: Request,
    secret_token: str = Header(
        default=None,
        alias="X-Telegram-Bot-Api-Secret-Token",
    ),
):
    if bot_id not in BOT_APPLICATIONS:
        raise HTTPException(
            status_code=404,
            detail="Unknown bot",
        )

    expected_secret = WEBHOOK_SECRETS[bot_id]

    if not secret_token or not secrets.compare_digest(
        secret_token,
        expected_secret,
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid webhook secret",
        )

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON",
        )

    if not isinstance(payload, dict) or "update_id" not in payload:
        raise HTTPException(
            status_code=400,
            detail="Invalid Telegram update",
        )

    bot_app = BOT_APPLICATIONS[bot_id]

    try:
        update = Update.de_json(payload, bot_app.bot)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Could not parse Telegram update",
        )

    await bot_app.update_queue.put(update)

    return {"ok": True}
