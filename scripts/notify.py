#!/usr/bin/env python3
"""웹훅 알림 전송 스크립트.

Discord, Slack, 또는 커스텀 웹훅 URL로 콘텐츠 생성 결과를 알립니다.
"""

import json
import os
import sys
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = PROJECT_ROOT / "posts"
REPORTS_DIR = PROJECT_ROOT / "reports"


def get_last_results() -> dict:
    results = {"post": None, "report": None}

    post_result = POSTS_DIR / ".last_result.json"
    if post_result.exists():
        with open(post_result, "r", encoding="utf-8") as f:
            results["post"] = json.load(f)

    report_result = REPORTS_DIR / ".last_result.json"
    if report_result.exists():
        with open(report_result, "r", encoding="utf-8") as f:
            results["report"] = json.load(f)

    return results


def build_message(results: dict) -> str:
    lines = ["📝 [블레스본부] 오늘의 콘텐츠 생성 완료!", ""]

    if results["post"]:
        post = results["post"]
        topic = post.get("topic", "")
        filename = Path(post.get("file", "")).name
        errors = post.get("errors", [])
        status = "✅" if not errors else "⚠️"
        lines.append(f'{status} AEO 블로그 포스트: "{topic}"')
        lines.append(f"   파일: {filename}")
        if errors:
            lines.append(f"   경고: {', '.join(errors)}")
    else:
        lines.append("❌ 블로그 포스트: 생성 실패")

    lines.append("")

    if results["report"]:
        report = results["report"]
        filename = Path(report.get("file", "")).name
        lines.append(f"✅ 보장분석 샘플 리포트: {filename}")
    else:
        lines.append("❌ 보장분석 리포트: 생성 실패")

    repo_url = os.environ.get("GITHUB_REPOSITORY", "hccho1204-dev/-")
    lines.append("")
    lines.append(f"📎 확인: https://github.com/{repo_url}/tree/main/posts")

    return "\n".join(lines)


def detect_webhook_type(url: str) -> str:
    if "discord.com/api/webhooks" in url or "discordapp.com/api/webhooks" in url:
        return "discord"
    elif "hooks.slack.com" in url:
        return "slack"
    return "custom"


def send_discord(url: str, message: str) -> bool:
    payload = {"content": message}
    resp = requests.post(url, json=payload, timeout=10)
    return resp.status_code in (200, 204)


def send_slack(url: str, message: str) -> bool:
    payload = {"text": message}
    resp = requests.post(url, json=payload, timeout=10)
    return resp.status_code == 200


def send_custom(url: str, message: str) -> bool:
    payload = {"text": message, "message": message}
    resp = requests.post(url, json=payload, timeout=10)
    return resp.status_code in range(200, 300)


def main():
    webhook_url = os.environ.get("WEBHOOK_URL")
    if not webhook_url:
        print("⚠️  WEBHOOK_URL이 설정되지 않았습니다. 알림을 건너뜁니다.")
        print("   GitHub Secrets에 WEBHOOK_URL을 추가해주세요.")
        return 0

    results = get_last_results()
    message = build_message(results)
    print("알림 메시지:")
    print(message)
    print()

    webhook_type = detect_webhook_type(webhook_url)
    print(f"웹훅 타입: {webhook_type}")

    senders = {"discord": send_discord, "slack": send_slack, "custom": send_custom}
    sender = senders[webhook_type]

    try:
        success = sender(webhook_url, message)
        if success:
            print("✅ 알림 전송 성공!")
            return 0
        else:
            print("❌ 알림 전송 실패")
            return 1
    except requests.RequestException as e:
        print(f"❌ 알림 전송 오류: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
