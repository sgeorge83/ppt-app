"""Sermon topics. Each list is a short set of references, not every verse that contains the word."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Topic:
    id: str
    label: str
    references: tuple[str, ...]


TOPICS: tuple[Topic, ...] = (
    Topic("love", "Love", ("John 3:16", "John 15:9-13", "Romans 5:8", "Romans 8:38-39", "1 Corinthians 13:4-7", "1 John 4:7-11", "John 13:34-35", "Ephesians 2:4-5")),
    Topic("faith", "Faith", ("Hebrews 11:1", "Hebrews 11:6", "Ephesians 2:8-9", "Romans 10:17", "Mark 11:22-24", "Habakkuk 2:4", "2 Corinthians 5:7", "James 2:17")),
    Topic("hope", "Hope", ("Romans 15:13", "Jeremiah 29:11", "Romans 8:24-25", "Hebrews 6:19", "Lamentations 3:21-23", "1 Peter 1:3", "Isaiah 40:31", "Psalm 42:11")),
    Topic("grace", "Grace", ("Ephesians 2:8-9", "2 Corinthians 12:9", "Romans 3:23-24", "Titus 2:11", "John 1:16-17", "Hebrews 4:16", "Romans 6:23", "James 4:6")),
    Topic("prayer", "Prayer", ("Matthew 6:9-13", "Philippians 4:6-7", "1 Thessalonians 5:16-18", "Jeremiah 33:3", "Matthew 7:7-8", "James 5:16", "Romans 8:26", "Psalm 145:18")),
    Topic("forgiveness", "Forgiveness", ("1 John 1:9", "Ephesians 4:32", "Colossians 3:13", "Matthew 6:14-15", "Psalm 103:12", "Isaiah 1:18", "Micah 7:18-19", "Romans 8:1")),
    Topic("salvation", "Salvation", ("John 3:16", "Romans 10:9-10", "Ephesians 2:8-9", "Acts 4:12", "Titus 3:5", "John 14:6", "Acts 16:31", "John 1:12")),
    Topic("peace", "Peace", ("John 14:27", "Philippians 4:6-7", "Isaiah 26:3", "Numbers 6:24-26", "Romans 5:1", "Colossians 3:15", "John 16:33", "Matthew 5:9")),
    Topic("comfort", "Comfort", ("2 Corinthians 1:3-4", "Psalm 23:4", "Matthew 11:28-30", "Psalm 34:18", "Revelation 21:4", "Isaiah 41:10", "Psalm 46:1", "Romans 8:28")),
    Topic("spirit", "Holy Spirit", ("John 14:26", "Acts 1:8", "Galatians 5:22-23", "Romans 8:26", "John 16:13", "Acts 2:38", "1 Corinthians 6:19", "Joel 2:28")),
    Topic("fear", "Fear", ("Isaiah 41:10", "2 Timothy 1:7", "Psalm 56:3", "Joshua 1:9", "1 John 4:18", "Deuteronomy 31:6", "Psalm 34:4", "Philippians 4:6-7")),
    Topic("strength", "Strength", ("Philippians 4:13", "Isaiah 40:31", "2 Corinthians 12:9-10", "Psalm 46:1", "Nehemiah 8:10", "Ephesians 6:10", "Psalm 28:7", "Joshua 1:9")),
)
