import os

from fetcher.note_fetcher import NoteFetcher
from prompt_builder.note.note_prompt_builder import NotePromptBuilder

CACHE_DIR = "cached_posts"
BASE_PROMPTS_DIR = "prompt_builder/note/base_prompts"

# 要約を生成するためのプロンプトの保存先
ABSTRACT_PROMPT_DIR = "prompt_builder/note/abstract_prompts"
# ブログ記事を生成するためのプロンプトの保存先
BODY_PROMPT_DIR = "prompt_builder/note/body_prompts"


def fetch_note_posts(profile_url: str, n_fetch: int | None = None) -> str:
    # プロファイルURLでNoteFetcherを初期化
    note_fetcher = NoteFetcher(
        profile_url=profile_url,
        cache_dir=CACHE_DIR,
    )

    posts = note_fetcher.get_all_posts(
        refetch=False,
    )
    print(f"取得された投稿の合計: {len(posts)}件")

    # 取得した内容をprompt用に表示する
    ret_text = [
        "*** 以下、過去の投稿 ***",
    ]

    # 直近n_fetchの記事のみ出力
    if n_fetch is None:
        # すべての記事を出力
        insert_posts = posts.sort_values(by=["published_at"], ascending=True)
        print("すべての記事を出力します")
    else:
        insert_posts = posts.sort_values(by=["published_at"], ascending=True).tail(n_fetch)
    print(f"直近記事{len(insert_posts):,}件を出力します")
    for _, post in insert_posts.iterrows():
        _insert_post = [
            "=" * 10,
            f"投稿タイトル: {post['title']}",
            f"投稿日時: {post['published_at']}",
            f"投稿URL: {post['noteURL']}",
            f"投稿内容: {post['content']}",
        ]
        ret_text.append("\n".join(_insert_post))
    ret_text.append("*** 以上、過去の投稿 ***")
    return "\n\n".join(ret_text)


def build_prompt(note_posts_text: str) -> str:
    prompt_builder = NotePromptBuilder(
        base_prompts_dir=BASE_PROMPTS_DIR,
    )
    return prompt_builder.build(note_posts_text)


def build_and_save_abstract_prompt(note_posts_text: str) -> None:
    """過去記事の要約を生成するためのプロンプトを生成し、保存する"""
    prompt_prefix = """
    以下に、過去のブログ記事の内容を記載します。
    各ブログについて、タイトル、投稿日、URLと記事の概要を記載してください。
    なお、概要は以下のルールに従ってください。
    - ルール1: 概要は300文字以内に収めてください
    - ルール2: 概要は、過去記事の内容を正確に反映してください
    
    例えば以下が概要のの例になります。
    
    ### 3. これまでの投資：長期投資のリアルな成功と失敗
    - 投稿日: 2025-03-15 21:32:04+09:00
    - URL: https://note.com/papa_salaryman/n/n0ff631681e04
    - 概要: 日本株・米国株・ETFへの長期投資経験と株主優待活用法を紹介。コロナショック時に恐怖で売却し後悔した体験から、感情に左右されない投資の重要性を説く。副業収入を投資に回す工夫や、配当と優待を合わせた総合利回りの考え方も解説している。

    なお、出力は過去のものから順に記載してください。
    
    以下が過去記事の内容です。
    """
    abstract_prompt = f"{prompt_prefix}\n\n{note_posts_text}"
    abstract_prompt_path = f"{ABSTRACT_PROMPT_DIR}/abstract_prompt.txt"
    os.makedirs(ABSTRACT_PROMPT_DIR, exist_ok=True)
    with open(abstract_prompt_path, "w", encoding="utf-8") as f:
        f.write(abstract_prompt)
    print(f"過去記事の要約プロンプトを保存しました: {abstract_prompt_path}")


def build_and_save_body_prompt(latest_post_text: str) -> None:
    """ブログ記事の本文を生成するためのプロンプトを生成し、保存する"""
    prompt = build_prompt(note_posts_text=latest_post_text)
    prompt_path = f"{BODY_PROMPT_DIR}/body_prompt.txt"
    os.makedirs(BODY_PROMPT_DIR, exist_ok=True)
    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write(prompt)
    print(f"ブログ記事の本文生成プロンプトを保存しました: {prompt_path}")


def main():
    """対象のNoteの投稿を取得し、記事生成用のプロンプトを作成する
    """
    profile_url = "https://note.com/papa_salaryman"
    note_posts_all_text = fetch_note_posts(
        profile_url=profile_url,
    )
    # 過去記事の要約を生成するためのプロンプトを生成し、保存する
    build_and_save_abstract_prompt(note_posts_all_text)

    latest_post_text = fetch_note_posts(
        profile_url=profile_url,
        n_fetch=1,
    )
    build_and_save_body_prompt(latest_post_text)


if __name__ == "__main__":
    main()