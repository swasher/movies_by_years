from parsel import Selector
import codecs

text = codecs.open("kinopoisk буду смотреть/1.html", "r", "utf-8").read()
selector = Selector(text=text)

ulli = selector.xpath('//ul[@id="itemList"]/li')
# print(ulli)
#
# a1=ulli[0]
# print(a1)
# a2=ulli[1]
# print('==================')
# print(a2)

count = 0
for x  in ulli:
    # movie = x.xpath("div[@class='info']/div/font/a/text()").get() # работает для сохраниний с 25 фильмами
    movie = x.xpath("div[@class='info']/a/text()").get()
    date_added = x.xpath("span/text()").get()[:10]

    count += 1
    print(count, date_added, movie)