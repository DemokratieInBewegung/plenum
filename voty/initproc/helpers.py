from .models import Initiative

def generate_initiative_from_random_wikipedia_article():
    import wikipedia
    wikipedia.set_lang('de')
    article = wikipedia.page(wikipedia.random())
    content = article.content
    chars = int(len(content) / 6)
    Initiative(title=article.title[:80],
               state='i',
               summary=content[0:chars],
               forderung=content[chars:chars*2],
               kosten=content[chars*2:chars*3],
               fin_vorschlag=content[chars*3:chars*4],
               arbeitsweise=content[chars*4:chars*5],
               init_argument=content[chars*5:chars*6]).save()