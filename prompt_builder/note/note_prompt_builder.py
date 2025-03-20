import os
from pathlib import Path
from typing import Optional


class NotePromptBuilder:
    """
    プロンプト構築クラス
    - prefix.txt: 冒頭に追加するテキスト
    - body.txt: プレースホルダーを含むメインコンテンツ
    - thema.txt: body.txtの{my_thema}プレースホルダーに挿入するテキスト
    """

    def __init__(self, base_prompts_dir: str = "base_prompts"):
        """
        NotePromptBuilderの初期化

        Args:
            base_prompts_dir: プロンプトコンポーネントファイルが保存されているディレクトリ
        """
        self.base_prompts_dir = Path(base_prompts_dir)
        self.prefix_text = ""
        self.body_text = ""
        self.thema_text = ""
        self.final_prompt = ""

    def load_prefix(self) -> str:
        """prefix.txtからプレフィックステキストを読み込む"""
        prefix_path = self.base_prompts_dir / "prefix.txt"
        try:
            with open(prefix_path, 'r', encoding='utf-8') as f:
                self.prefix_text = f.read()
            return self.prefix_text
        except FileNotFoundError:
            print(f"警告: {prefix_path} が見つかりません")
            return ""

    def load_body(self) -> str:
        """body.txtから本文テキストを読み込む"""
        body_path = self.base_prompts_dir / "body.txt"
        try:
            with open(body_path, 'r', encoding='utf-8') as f:
                self.body_text = f.read()
            return self.body_text
        except FileNotFoundError:
            print(f"エラー: {body_path} が見つかりません")
            self.body_text = ""
            return ""

    def load_thema(self) -> str:
        """thema.txtからテーマテキストを読み込む"""
        thema_path = self.base_prompts_dir / "thema.txt"
        try:
            with open(thema_path, 'r', encoding='utf-8') as f:
                self.thema_text = f.read()
            return self.thema_text
        except FileNotFoundError:
            print(f"警告: {thema_path} が見つかりません")
            return ""

    def build(self, history_posts: str) -> str:
        """
        最終的なプロンプトを構築する:
        1. すべてのテキストコンポーネントを読み込む
        2. 本文の先頭にプレフィックスを挿入
        3. {my_thema}プレースホルダーをテーマで置換

        Returns:
            完成したプロンプトテキスト
        """
        # すべてのテキストコンポーネントを読み込む
        self.load_prefix()
        self.load_body()
        self.load_thema()

        if not self.body_text:
            raise ValueError("本文テキストが必要ですが、見つからないか空です")

        # プレフィックスと本文を結合
        combined_text = self.prefix_text + self.body_text if self.prefix_text else self.body_text

        # 過去の記事を挿入
        self.final_prompt = combined_text.replace("{history_posts}", history_posts)

        # プレースホルダーをテーマで置換
        self.final_prompt = self.final_prompt.replace("{my_thema}", self.thema_text)

        return self.final_prompt
