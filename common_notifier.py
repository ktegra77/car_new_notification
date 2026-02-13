import requests

def send_discord_message(webhook_url, message):
    """DiscordのWebhookにメッセージを送信する関数"""
    data = {"content": message}
    response = requests.post(webhook_url, json=data)
    return response.status_code

if __name__ == "__main__":
    # テスト用
    WEBHOOK_URL = "https://discord.com/api/webhooks/1471129979545977086/qR3Y6Z054rLxDffdqgoB6oQWuTZWmn6s0AZ5rkpGFIF49gp-VwSG9rQWQutqh333iEie"
    send_discord_message(WEBHOOK_URL, "システム起動：車探しを開始します！")