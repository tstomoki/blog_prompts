from fetcher.note_fetcher import NoteFetcher
from prompt_builder.note.note_prompt_builder import NotePromptBuilder

CACHE_DIR = "cached_posts"
BASE_PROMPTS_DIR = "prompt_builder/note/base_prompts"


def fetch_note_posts(profile_url: str) -> str:
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
    for _, post in posts.iterrows():
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



def main():
    """対象のNoteの投稿を取得し、記事生成用のプロンプトを作成する
    """
    profile_url = "https://note.com/papa_salaryman"
    note_posts_text = fetch_note_posts(
        profile_url=profile_url,
    )
    prompt = build_prompt(note_posts_text=note_posts_text)

    print(prompt)


if __name__ == "__main__":
    main()