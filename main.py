import os
import datetime
import sys

# 抽出対象とするファイルの拡張子と、Markdownで使う言語名を対応させます
TARGET_EXTENSIONS = {
    '.py': 'python',
    '.html': 'html',
    '.css': 'css',
    '.js': 'javascript',
    '.json': 'json',
    '.txt': 'text',
    '.md': 'markdown'
}

USE_FIXED_PATH = False  # True: 固定パスを使用 / False: 毎回入力する
FIXED_TARGET_PATH = r"C:\Users\tsuts\Desktop\ワークスペース\universal_improving_system"

def create_full_documentation(target_path):
    """
    指定フォルダのファイル構造と対象ソースコードを抽出し、
    1つのMarkdownファイルとして保存します。
    """
    target_path = target_path.strip().strip('"').strip("'")

    if not os.path.isdir(target_path):
        print(f"❌ エラー: フォルダ '{target_path}' が見つかりません。")
        return

    # --- 0. sfs_ignore の読み込み ---
    code_ignore_list = []
    ignore_file_path = os.path.join(target_path, "sfs_ignore")
    if os.path.exists(ignore_file_path):
        try:
            with open(ignore_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # 空行とコメントを除外
                    if line and not line.startswith('#'):
                        # Windows/Macのパス区切り差異を吸収するため / に統一して保存
                        code_ignore_list.append(line.rstrip('/').replace('\\', '/'))
            print(f"ℹ️  sfs_ignore を読み込みました: {code_ignore_list}")
        except Exception as e:
            print(f"⚠️  sfs_ignore の読み込み中にエラーが発生しました: {e}")

    # --- 1. ツリー構造を生成 & 対象ファイルをリストアップ ---
    def build_tree_and_find_code(dir_path, prefix="", current_rel_dir=""):
        lines = []
        try:
            # 完全に無視する（Treeにも出さない）基本設定
            exclude = ['.git', '__pycache__', '.vscode', '.DS_Store', 'venv', '.env']
            entries = sorted([e for e in os.listdir(dir_path) if e not in exclude])
        except PermissionError:
            return [f"{prefix}└── [アクセス権がありません]"], []

        local_code_files = []
        for i, entry in enumerate(entries):
            is_last = (i == len(entries) - 1)
            connector = "└── " if is_last else "├── "
            path = os.path.join(dir_path, entry)
            
            # ルートからの相対パスを作成（sfs_ignore判定用）
            # 例: data/OtherCorp
            rel_path = os.path.join(current_rel_dir, entry).replace(os.sep, '/')

            # sfs_ignore に該当するかチェック
            is_ignored_for_code = False
            for ignore_item in code_ignore_list:
                # 完全に一致するか、その配下のパスであるかを確認
                if rel_path == ignore_item or rel_path.startswith(ignore_item + "/"):
                    is_ignored_for_code = True
                    break

            # 対象の拡張子を持ち、かつignoreリストに入っていない場合のみ抽出対象にする
            ext = os.path.splitext(entry)[1].lower()
            if ext in TARGET_EXTENSIONS and not is_ignored_for_code:
                local_code_files.append(rel_path)

            if os.path.isdir(path):
                lines.append(f"{prefix}{connector}{entry}/")
                extension = "    " if is_last else "│   "
                # 再帰呼び出し
                sub_lines, sub_code_files = build_tree_and_find_code(path, prefix + extension, rel_path)
                lines.extend(sub_lines)
                local_code_files.extend(sub_code_files)
            else:
                lines.append(f"{prefix}{connector}{entry}")
        
        return lines, local_code_files

    # --- 2. コンテンツの作成 ---
    base_folder_name = os.path.basename(os.path.abspath(target_path)) or "root"
    date_str = datetime.datetime.now().strftime('%Y年%m月%d日')
    
    description = (
        f"# 📁 {base_folder_name} のファイル構造とソースコード\n\n"
        f"**作成日:** {date_str}\n\n"
        f"**対象フォルダ:** `{target_path}`\n\n"
    )

    print("📂 フォルダ構造を解析中...")
    tree_lines, code_files_relative = build_tree_and_find_code(target_path)
    
    tree_markdown = (
        "## ファイル構造\n"
        "```\n"
        f"{base_folder_name}/\n" +
        "\n".join(tree_lines) +
        "\n```\n"
    )

    source_code_docs = ["\n---\n\n## 各ファイルのソースコード\n"]
    print(f"📄 ソースコード抽出中 ({len(code_files_relative)} ファイル)...")
    
    for relative_path in sorted(code_files_relative):
        full_path = os.path.join(target_path, relative_path)
        ext = os.path.splitext(relative_path)[1].lower()
        lang = TARGET_EXTENSIONS.get(ext, "")
        
        header_path = relative_path.replace(os.sep, '/')
        source_code_docs.append(f"### 📄 {header_path}\n")
        
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            source_code_docs.append(f"```{lang}\n{content}\n```\n\n")
        except Exception as e:
            source_code_docs.append(f"```\n[エラー: ファイルを読み込めませんでした - {e}]\n```\n\n")

    final_content = description + tree_markdown + "".join(source_code_docs)

    # --- 3. 保存 ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    output_filename = f"doc_{base_folder_name}_{datetime.datetime.now().strftime('%H%M%S')}.md"
    output_filepath = os.path.join(output_dir, output_filename)

    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(final_content)
        print(f"✅ 完了！ドキュメントを保存しました:\n   {output_filepath}")
    except Exception as e:
        print(f"❌ ファイルの保存中にエラーが発生しました: {e}")

if __name__ == '__main__':
    print("=== Source to Markdown Converter (with sfs_ignore) ===")
    if USE_FIXED_PATH:
        input_path = FIXED_TARGET_PATH
    else:
        input_path = input("変換したいフォルダのパスを入力してEnterを押してください:\n> ")
    
    if input_path and input_path.strip():
        create_full_documentation(input_path)