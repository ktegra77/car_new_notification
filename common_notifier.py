import os
import logging
import requests
from typing import Optional
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# ログの設定
logger = logging.getLogger(__name__)

def send_discord_notification(message: str, webhook_url: Optional[str] = None) -> bool:
    """
    DiscordのWebhookへメッセージを送信します。

    Args:
        message (str): 送信するテキストメッセージ
        webhook_url (Optional[str]): DiscordのWebhook URL。
            指定がない場合は環境変数 'DISCORD_WEBHOOK_URL' から取得します。

    Returns:
        bool: 送信に成功した場合はTrue、失敗した場合はFalse
    """

    target_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")

    if not target_url or not target_url.startswith("http"):
        logger.error(f"Discord Webhook URLが設定されていないか、不正です: {target_url}")
        return False

    payload = {"content": message}

    try:
        response = requests.post(target_url, json=payload, timeout=10)
        
        # ステータスコードが200番台以外（エラー）の場合、例外を発生させる
        response.raise_for_status()
        return True

    except requests.RequestException as e:
        logger.error(f"Discordへの送信中にエラーが発生しました: {e}")
        return False

if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(level=logging.INFO)
    
    # テスト送信
    test_msg = "🛠 【システムテスト】通知モジュールのリファクタリングが完了しました。"
    
    if send_discord_notification(test_msg):
        print("送信成功")
    else:
        print("送信失敗（URLが設定されていないか、通信エラーです）")