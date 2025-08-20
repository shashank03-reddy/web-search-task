import requests
from bs4 import BeautifulSoup
from collections import defaultdict
from urllib.parse import urljoin, urlparse
import unittest
from unittest.mock import patch, MagicMock


class WebCrawler:
    def __init__(self, same_domain=True, base_domain=None):
        self.index = defaultdict(str)
        self.visited = set()
        self.same_domain = same_domain
        self.base_domain = base_domain

    def crawl(self, url, base_url=None):
        if url in self.visited:
            return
        self.visited.add(url)

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            self.index[url] = soup.get_text()

            for link in soup.find_all('a', href=True):
                href = link['href']
                abs_url = urljoin(base_url or url, href)
                parsed = urlparse(abs_url)

                if self.same_domain:
                    if parsed.netloc == (self.base_domain or urlparse(url).netloc):
                        self.crawl(abs_url, base_url=base_url or url)
                else:
                    self.crawl(abs_url, base_url=base_url or url)

        except Exception as e:
            print(f"Error crawling {url}: {e}")

    def search(self, keyword):
        results = []
        for url, text in self.index.items():
            if keyword.lower() in text.lower():
                results.append(url)
        return results

    def print_results(self, results):
        if results:
            print("Search results:")
            for url in results:
                print(f"- {url}")
        else:
            print("No results found.")


class WebCrawlerTests(unittest.TestCase):
    @patch('requests.get')
    def test_crawl_success(self, mock_get):
        sample_html = """
        <html><body>
            <h1>Welcome!</h1>
            <a href="/about">About Us</a>
            <a href="https://www.external.com">External Link</a>
        </body></html>
        """
        mock_response = MagicMock()
        mock_response.text = sample_html
        mock_response.raise_for_status = lambda: None
        mock_get.return_value = mock_response

        crawler = WebCrawler()
        crawler.crawl("https://example.com")

        self.assertIn("https://example.com/about", crawler.visited)

    @patch('requests.get')
    def test_crawl_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException("Test Error")

        crawler = WebCrawler()
        crawler.crawl("https://example.com")

        self.assertIn("https://example.com", crawler.visited)

    @patch('requests.get')
    def test_same_domain_restriction(self, mock_get):
        html = """
        <html><body>
            <a href="/internal">Internal</a>
            <a href="https://external.com/page">External</a>
        </body></html>
        """
        mock_response = MagicMock()
        mock_response.text = html
        mock_response.raise_for_status = lambda: None
        mock_get.return_value = mock_response

        crawler = WebCrawler(same_domain=True, base_domain="example.com")
        crawler.crawl("https://example.com")

        self.assertIn("https://example.com/internal", crawler.visited)
        self.assertNotIn("https://external.com/page", crawler.visited)

    @patch('requests.get')
    def test_allow_external_when_disabled(self, mock_get):
        html = '<html><body><a href="https://external.com/page">External</a></body></html>'
        mock_response = MagicMock()
        mock_response.text = html
        mock_response.raise_for_status = lambda: None
        mock_get.return_value = mock_response

        crawler = WebCrawler(same_domain=False)
        crawler.crawl("https://example.com")

        self.assertIn("https://external.com/page", crawler.visited)

    def test_duplicate_visit(self):
        crawler = WebCrawler()
        crawler.visited.add("https://example.com")
        crawler.crawl("https://example.com")  # should skip re-crawl
        self.assertEqual(len(crawler.visited), 1)

    def test_empty_page(self):
        crawler = WebCrawler()
        crawler.index["empty"] = ""
        self.assertEqual(crawler.search("anything"), [])

    def test_search_single_match(self):
        crawler = WebCrawler()
        crawler.index["page1"] = "This has the keyword"
        crawler.index["page2"] = "No match here"
        results = crawler.search("keyword")
        self.assertEqual(results, ["page1"])

    def test_search_multiple_matches(self):
        crawler = WebCrawler()
        crawler.index["page1"] = "Python crawler"
        crawler.index["page2"] = "Another Python page"
        crawler.index["page3"] = "No match here"
        results = crawler.search("python")
        self.assertEqual(set(results), {"page1", "page2"})

    def test_search_case_insensitive(self):
        crawler = WebCrawler()
        crawler.index["page1"] = "HELLO World"
        results = crawler.search("hello")
        self.assertEqual(results, ["page1"])

    def test_search_not_found(self):
        crawler = WebCrawler()
        crawler.index["page1"] = "No relevant data"
        results = crawler.search("missing")
        self.assertEqual(results, [])

    def test_print_results(self):
        crawler = WebCrawler()
        results = ["https://test.com/result"]

        with patch("builtins.print") as mock_print:
            crawler.print_results(results)
            mock_print.assert_any_call("Search results:")
            mock_print.assert_any_call("- https://test.com/result")

    def test_print_no_results(self):
        crawler = WebCrawler()
        with patch("builtins.print") as mock_print:
            crawler.print_results([])
            mock_print.assert_any_call("No results found.")


def main():
    crawler = WebCrawler()
    start_url = "https://example.com"
    crawler.crawl(start_url)

    keyword = "test"
    results = crawler.search(keyword)
    crawler.print_results(results)


if __name__ == "__main__":
    # Run main demo
    main()
    # Run unit tests
    print("\n--- Running Unit Tests ---")
    unittest.main(argv=["first-arg-is-ignored"], exit=False)
