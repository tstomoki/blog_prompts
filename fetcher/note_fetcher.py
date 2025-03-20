import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
from typing import List, Dict, Optional, Any
from datetime import datetime
import os
import glob
import hashlib


class NoteFetcher:
    def __init__(self, profile_url: str, cache_dir: str = "cached_posts"):
        """
        NoteFetcherの初期化

        Args:
            profile_url: 投稿を取得する基本URL (例: "https://note.com/papa_salaryman")
            cache_dir: HTMLキャッシュを保存するディレクトリ
        """
        self.profile_url: str = profile_url
        self.cache_dir: str = cache_dir
        self.session: requests.Session = requests.Session()
        self.headers: Dict[str, str] = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        # プロフィールURLからユーザー名を抽出
        self.username: str = profile_url.split("/")[-1]

        # 必要なディレクトリの作成
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def fetch_api_data(self, page: int = 1) -> Optional[Dict[str, Any]]:
        """
        APIから記事リストデータを取得

        Args:
            page: 取得するページ番号

        Returns:
            API応答データ、エラー時はNone
        """
        api_url = f"https://note.com/api/v2/creators/{self.username}/contents?kind=note&page={page}"

        try:
            response = self.session.get(api_url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API {api_url} の取得中にエラーが発生: {e}")
            return None

    def fetch_article_content(self, note_url: str, refetch: bool = False) -> Optional[Dict[str, Any]]:
        """
        記事の本文を取得し、画像やリンクを特定できる形式で保持

        Args:
            note_url: 記事のURL
            refetch: キャッシュを無視して再取得するかどうか

        Returns:
            記事の本文、エラー時はNone
        """
        # URLからキャッシュファイル名を生成
        url_hash = hashlib.md5(note_url.encode()).hexdigest()[:10]
        cache_path = f"{self.cache_dir}/html_cache_{url_hash}.html"

        # キャッシュがあり、再取得しない場合はキャッシュを使用
        if not refetch and os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    print(f"キャッシュされたHTMLを使用: {note_url}")
                    html = f.read()
            except Exception as e:
                print(f"HTMLキャッシュの読み込みに失敗しました: {e}")
                html = None
        else:
            html = None

        # キャッシュがなければ新しく取得
        if not html:
            try:
                response = self.session.get(note_url, headers=self.headers)
                response.raise_for_status()
                html = response.text

                # HTMLをキャッシュ
                with open(cache_path, 'w', encoding='utf-8') as f:
                    f.write(html)
            except requests.exceptions.RequestException as e:
                print(f"記事 {note_url} の取得中にエラーが発生: {e}")
                return None

        # HTMLをパース
        soup = BeautifulSoup(html, 'html.parser')

        # 記事の本文要素を取得
        article_content = soup.select_one('div.note-common-styles__textnote-body')

        if not article_content:
            print(f"記事の本文が見つかりませんでした: {note_url}")
            return None

        # リンクをテキスト表現に変換（例: "リンクテキスト [URL: https://example.com]"）
        for a_tag in article_content.select('a'):
            href = a_tag.get('href', '')
            if href:
                link_text = a_tag.text.strip()
                a_tag.replace_with(f"{link_text} [URL: {href}]")

        # 画像をテキスト表現に変換 （例: "[画像: https://example.com/image.jpg]"）
        for img_tag in article_content.select('img'):
            src = img_tag.get('src', '')
            alt = img_tag.get('alt', '画像')
            if src:
                img_tag.replace_with(f"[{alt}: {src}]")

        # 変換後の本文テキストを取得
        text_content = article_content.get_text(separator='\n').strip()

        return {
            "content": text_content
        }

    def get_all_posts(self, refetch: bool = False) -> pd.DataFrame:
        """
        すべての記事を取得してDataFrameとして返す

        Args:
            refetch: True の場合、既存のHTMLキャッシュを削除して再取得する

        Returns:
            記事データを含むDataFrame
        """
        # refetch=True の場合、既存のHTMLキャッシュを削除
        if refetch:
            # HTML キャッシュファイルのパターン
            cache_pattern = f"{self.cache_dir}/html_cache_*.html"
            cache_files = glob.glob(cache_pattern)

            if cache_files:
                print(f"キャッシュをクリア中... {len(cache_files)}ファイルを削除します")
                for cache_file in cache_files:
                    try:
                        os.remove(cache_file)
                    except OSError as e:
                        print(f"ファイル {cache_file} の削除中にエラーが発生: {e}")

        all_articles = []
        page = 1
        has_next = True

        # ページネーションを使用してすべての記事を取得
        while has_next:
            print(f"APIからページ {page} を取得中...")
            data = self.fetch_api_data(page)

            if not data or "data" not in data or "contents" not in data["data"]:
                print(f"ページ {page} からのデータ取得に失敗しました")
                break

            contents = data["data"]["contents"]
            if not contents:
                break

            # 各記事の基本情報を抽出
            for article in contents:
                try:
                    published_at = article.get("publishAt", "")
                    if published_at:
                        # ISO 8601形式の日時文字列をdatetimeオブジェクトに変換
                        published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))

                    article_info = {
                        "published_at": published_at,
                        "title": article.get("name", ""),
                        "noteURL": f"https://note.com/{self.username}/n/{article.get('key', '')}"
                    }
                    all_articles.append(article_info)
                except Exception as e:
                    print(f"記事データの処理中にエラーが発生: {e}")

            # 次のページがあるか確認
            has_next = data["data"].get("isLastPage", True) is False
            page += 1

            # APIリクエスト間の遅延
            time.sleep(1)

        print(f"合計 {len(all_articles)} 件の記事基本情報を取得しました")

        # 各記事の本文を取得
        for i, article in enumerate(all_articles):
            print(f"記事 {i + 1}/{len(all_articles)} の本文を取得中: {article['title']}")
            content_data = self.fetch_article_content(article["noteURL"], refetch=refetch)

            if content_data:
                article["content"] = content_data["content"]
            else:
                article["content"] = ""

        # DataFrameに変換
        df = pd.DataFrame(all_articles)

        # 必要な列を選択して並べ替え
        columns = ["published_at", "title", "noteURL", "content"]
        df = df[columns]
        # published_atでソート
        df.sort_values(by="published_at", ascending=True, inplace=True)

        print(f"すべての記事データを取得完了: {len(df)}件")
        return df