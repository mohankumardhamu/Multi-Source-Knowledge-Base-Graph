from __future__ import annotations

from libs.common.kg_rag_common.classify import detect_language, detect_topics, classify_document


def test_detect_language_python_simple():
    text = """
    def foo(x):
        print(x)
    class Bar(object):
        pass
    """
    assert detect_language(text) == "python"


def test_detect_language_go_vs_csharp_prefers_go():
    text = """
    package main
    import "fmt"
    func main() {
        fmt.Println("hi")
        go worker()
    }
    """
    assert detect_language(text) == "go"


def test_detect_language_none_for_plain_text():
    text = "This is a plain paragraph without code."
    assert detect_language(text) is None


def test_detect_topics_multiple():
    text = "Using HTTP client to send requests to server; handle async/await and sockets."
    topics = detect_topics(text)
    assert "networking" in topics
    assert "concurrency" in topics


def test_classify_document_union_topics_and_best_language():
    t1 = "public static void main(String[] args) { System.out.println(1); }"
    t2 = "Perform BFS on the graph; O(n log n) complexity."
    lang, topics = classify_document([t1, t2])
    assert lang == "java"
    assert "algorithms" in topics

