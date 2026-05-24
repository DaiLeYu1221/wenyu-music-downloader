import os
from api_client import MusicAPI
from downloader import MusicDownloader
from config import PLATFORMS


class MusicCLI:
    """Interactive CLI for music search and download."""

    def __init__(self):
        self.current_results = []
        self.current_platform = None
        self.current_keyword = None
        self.save_dir = "./downloads"

    def run(self):
        """Main loop."""
        self._print_banner()

        while True:
            try:
                self._print_menu()
                choice = input("\n请输入选项 > ").strip()

                if choice == "1":
                    self._search_and_download()
                elif choice == "2":
                    self._change_platform()
                elif choice == "0":
                    print("再见！")
                    break
                else:
                    print("无效选项，请重新输入")
            except KeyboardInterrupt:
                print("\n再见！")
                break
            except Exception as e:
                print(f"\n错误: {e}")

    def _print_banner(self):
        print("=" * 50)
        print("          文宇音乐聚合搜索 & 下载器")
        print("=" * 50)

    def _print_menu(self):
        platform_name = PLATFORMS.get(self.current_platform, {}).get("name", "未选择")
        print(f"\n当前平台: {platform_name}")
        print("-" * 40)
        print("  1. 搜索并下载音乐")
        print("  2. 切换音乐平台")
        print("  0. 退出")

    def _select_platform(self):
        """Let user select a music platform."""
        print("\n可选音乐平台:")
        platforms = list(PLATFORMS.keys())
        for i, key in enumerate(platforms, 1):
            print(f"  {i}. {PLATFORMS[key]['name']}")

        while True:
            try:
                choice = input("选择平台编号 > ").strip()
                if not choice:
                    continue
                idx = int(choice)
                key = platforms[idx - 1]
                self.current_platform = key
                self.current_results = []
                self.current_keyword = None
                print(f"已选择: {PLATFORMS[key]['name']}")
                return key
            except (ValueError, IndexError):
                print("无效选择，请重新输入")

    def _search_and_download(self):
        """Search for music and directly download."""
        if not self.current_platform:
            self._select_platform()

        keyword = input("输入搜索关键词 > ").strip()
        if not keyword:
            print("关键词不能为空")
            return

        try:
            print(f"\n正在搜索: {keyword} ...")
            data = MusicAPI.search(self.current_platform, keyword)

            songs = data.get("songs", [])
            if not songs:
                print("未找到结果")
                return

            self.current_results = songs
            self.current_keyword = keyword

            print(f"\n搜索结果 ({PLATFORMS[self.current_platform]['name']}):")
            print("-" * 40)
            for song in songs:
                n = song.get("n", "?")
                name = song.get("name", "未知")
                singer = song.get("singer", "未知")
                album = song.get("album", "")
                print(f"  {n}. {name} - {singer}  ({album})")
            print("-" * 40)

            while True:
                try:
                    idx = int(input("选择歌曲编号下载 (0 返回) > ").strip())
                    if idx == 0:
                        return

                    found_song = None
                    for s in self.current_results:
                        if s.get("n") == idx:
                            found_song = s
                            break

                    if not found_song:
                        print("未找到该编号的歌曲，请重新输入")
                        continue

                    song_mid = found_song.get("mid") or found_song.get("rid")

                    print("\n开始下载...")
                    MusicDownloader.download(
                        self.current_platform, idx, self.current_keyword,
                        save_dir=self.save_dir, show_progress=True,
                        song_mid=song_mid,
                    )
                    print("下载完成！")
                    return

                except ValueError:
                    print("请输入有效数字")

        except Exception as e:
            print(f"搜索失败: {e}")

    def _change_platform(self):
        """Change music platform."""
        self._select_platform()


def main():
    cli = MusicCLI()
    cli.run()


if __name__ == "__main__":
    main()
