import os
import random
import re
import sys

DAMPING = 0.85
SAMPLES = 10000


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python pagerank.py corpus")
    corpus = crawl(sys.argv[1])
    ranks = sample_pagerank(corpus, DAMPING, SAMPLES)
    print(f"PageRank Results from Sampling (n = {SAMPLES})")
    for page in sorted(ranks):
        print(f"  {page}: {ranks[page]:.4f}")
    ranks = iterate_pagerank(corpus, DAMPING)
    print(f"PageRank Results from Iteration")
    for page in sorted(ranks):
        print(f"  {page}: {ranks[page]:.4f}")


def crawl(directory):
    """
    Parse a directory of HTML pages and check for links to other pages.
    Return a dictionary where each key is a page, and values are
    a list of all other pages in the corpus that are linked to by the page.
    """
    pages = dict()

    # Extract all links from HTML files
    for filename in os.listdir(directory):
        if not filename.endswith(".html"):
            continue
        with open(os.path.join(directory, filename)) as f:
            contents = f.read()
            links = re.findall(r"<a\s+(?:[^>]*?)href=\"([^\"]*)\"", contents)
            pages[filename] = set(links) - {filename}

    # Only include links to other pages in the corpus
    for filename in pages:
        pages[filename] = set(
            link for link in pages[filename]
            if link in pages
        )

    return pages


def transition_model(corpus, page, damping_factor):
    """
    Return a probability distribution over which page to visit next,
    given a current page.

    With probability `damping_factor`, choose a link at random
    linked to by `page`. With probability `1 - damping_factor`, choose
    a link at random chosen from all pages in the corpus.
    """

    model = dict()
    damping_complement = 1 - damping_factor
    damping_probability = damping_complement/len(corpus)

    if corpus[page] != set():
        for file in corpus:
            if file in corpus[page]:
                model[file] = damping_factor/len(corpus[page]) + damping_probability
            else:
                model[file] = damping_probability
    else:
        for file in corpus:
            model[file] = damping_probability

    return model


def sample_pagerank(corpus, damping_factor, n):
    """
    Return PageRank values for each page by sampling `n` pages
    according to transition model, starting with a page at random.

    Return a dictionary where keys are page names, and values are
    their estimated PageRank value (a value between 0 and 1). All
    PageRank values should sum to 1.
    """

    page_rank = dict()
    for page in corpus:
        page_rank[page] = 0

    sample = random.choice(list(corpus.keys()))
    page_rank[sample] += 1

    for i in range(1, n):
        model = transition_model(corpus, sample, damping_factor)
        sample = random.choices(list(model.keys()), list(model.values()), k=1)[0]
        page_rank[sample] += 1

    for page in page_rank:
        page_rank[page] /= n

    return page_rank


def iterate_pagerank(corpus, damping_factor):
    """
    Return PageRank values for each page by iteratively updating
    PageRank values until convergence.

    Return a dictionary where keys are page names, and values are
    their estimated PageRank value (a value between 0 and 1). All
    PageRank values should sum to 1.
    """
    
    page_rank = dict()
    n = len(corpus)

    for page in corpus:
        page_rank[page] = 1/n


    while True:
        i = 0
        for page_p in page_rank:
            sum = 0
            for page_i in page_rank:
                if page_p in corpus[page_i]:
                    sum += page_rank[page_i]/len(corpus[page_i])

            new_value = (1-damping_factor)/n + damping_factor * sum
            e = abs(page_rank[page_p] - new_value)
            page_rank[page_p] = new_value

            if e < 0.001:
                i += 1

        if i == len(page_rank):
            break
    
    return page_rank



if __name__ == "__main__":
    main()
