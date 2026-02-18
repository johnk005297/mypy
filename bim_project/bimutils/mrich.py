class ScrollablePanel:
    def __init__(self, data, title="Scrollable List", subtitle="", subtitle_align="center", height=8, width=90):
        self.data = data
        self.title = title
        self.height = height
        self.width = width
        self.subtitle = subtitle
        self.subtitle_align = subtitle_align
        self.scroll_position = 0
        # self.console = Console()

    def get_visible_data(self):
        """Get the currently visible portion of data"""
        end_pos = min(self.scroll_position + self.height, len(self.data))
        return self.data[self.scroll_position:end_pos]

    def get_panel(self):
        """Generate the panel with current scroll position"""
        from rich.panel import Panel
        from rich.text import Text

        visible_data = self.get_visible_data()

        display_text = Text(overflow="ellipsis")
        for i, item in enumerate(visible_data, self.scroll_position + 1):
            display_text.append(f"{i:3d}. {str(item)}\n")

        return Panel(
            display_text,
            title=f"{self.title} [{self.scroll_position + 1}-{self.scroll_position + len(visible_data)}/{len(self.data)}]",
            border_style="blue",
            subtitle=self.subtitle,
            subtitle_align = self.subtitle_align,
            width=self.width
        )

    def auto_scroll(self, delay=0.5):
        """Automatically scroll through the list"""
        import time
        from rich.live import Live
        with Live(self.get_panel(), refresh_per_second=4) as live:
            for i in range(len(self.data) - self.height + 1):
                self.scroll_position = i
                live.update(self.get_panel())
                time.sleep(delay)


    # # Example usage
    # if __name__ == "__main__":
    #     # Sample data (replace with your list)
    #     sample_data = [
    #         f"Item {i}: This is line number {i} with some sample text"
    #         for i in range(1, 26)
    #     ]

    #     # Create scrollable panel
    #     panel = ScrollablePanel(sample_data, title="Scrollable Data", height=8, width=65)

    #     # Option 1: Auto-scroll (like automatic scrolling)
    #     print("Auto-scrolling demo:")
    #     panel.auto_scroll(delay=0.3)
