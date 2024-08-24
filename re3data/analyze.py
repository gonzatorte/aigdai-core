from .extractor import load_from_file
import pandas
import matplotlib.pyplot as plt
import seaborn


def analyze():
    # repository_info = pandas.DataFrame(results)
    # repository_info = repository_info.apply(pandas.Series.explode)
    # repository_info["api_type"] = repository_info["api_type"].astype("category")
    # repository_info.sort_values(by="re3data_id", inplace=True)

    results = load_from_file()
    repository_info = pandas.DataFrame(results)
    repository_info = repository_info.apply(pandas.Series.explode)
    repository_info["re3data.orgidentifier"] = repository_info["re3data.orgidentifier"].astype("string")
    repository_info["repositoryName"] = repository_info["repositoryName"].astype("string")
    repository_info["repositoryURL"] = repository_info["repositoryURL"].astype("string")
    cat_type = pandas.CategoricalDtype(categories=map(lambda x: x.lower(), [
        "CKAN",
        "DataVerse",
        "DigitalCommons",
        "dLibra",
        "DSpace",
        "EPrints",
        "eSciDoc",
        "Fedora",
        "MySQL",
        "Nesstar",
        "Opus",
        "other",
        "unknown",
        "none",  # I added this category
    ]), ordered=True)
    repository_info["softwareNames"] = repository_info["softwareNames"].map(
        lambda x: x[0].lower() if x is not None else "none"
    ).astype(cat_type)
    repository_info.sort_values(by="re3data.orgidentifier", inplace=True)

    seaborn.set_style("whitegrid")

    def plot_by(dimension_name: str):
        plt.figure(figsize=(10, 5))
        ax = seaborn.countplot(
            x=dimension_name,
            data=repository_info.drop_duplicates(subset=["re3data.orgidentifier", dimension_name]),
            order=repository_info[dimension_name].value_counts().index,
        )
        ax.bar_label(ax.containers[0])
        ax.set(
            title="%s types for re3data repositories" % dimension_name
        )
        plt.show()

    plot_by("softwareNames")
    # plotBy("softwareName")


if __name__ == '__main__':
    analyze()
