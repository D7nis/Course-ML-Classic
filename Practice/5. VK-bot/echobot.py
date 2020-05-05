# -*- coding: utf-8 -*-
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.upload import VkUpload

import random
import argparse
import traceback

import re
from skimage import io, img_as_float
from sklearn.cluster import KMeans

# Эхо бот
# https://github.com/python273/vk_api
# Документация по python vk api с примерами
# https://vk.com/dev/manuals
# Общая документация по vk api


VK_TOKEN = 'a2a0075....'
GROUP_ID = 0# пример 194690777
# Напишите сюда свой токен и id группы.


def parse_args():
    parser = argparse.ArgumentParser()  # Для параметров
    parser.add_argument('--vk_token', type=str, default=VK_TOKEN)
    parser.add_argument('--vk_group_id', type=int, default=GROUP_ID)
    return parser.parse_args()


def main():
    params = parse_args()

    vk_session = vk_api.VkApi(token=params.vk_token)
    uploader = VkUpload(vk_session)  # Понадобится для загрузки своих изображений в вк
    long_poll = VkBotLongPoll(vk_session, params.vk_group_id)

    flag_first_message = True # Первое сообщение, флаг.

    for event in long_poll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            print(type(event.obj))
            print(event.obj)  # Тут хранится все инфорация о сообщении
            print()

            message = event.obj.message
            peer_id = message['peer_id']  # ID пользователя куда отсылать ответ
            from_id = message['from_id']  # ID пользователя который прислал сообщение
            text = message['text']  # Текст сообщения
            text_answer = '' #Текст ответа пользователю
            text_answer_kmeans = ''#Текст ответа, если  пользователь ввел число кластеров

            text_example = "Кинь картнику и введи количество цветов вот так: colors=5"

            attachments = message['attachments']  # Вложенные файлы(это и изображения и музыка и видео и т.д)
            print(type(attachments))  # Так как их может быть несколько это список
            print(attachments)
            print()

            if len(attachments) > 0 and attachments[0]['type'] == 'photo':
                photo = attachments[0]['photo']
                print(type(photo))
                print(photo)
                print()
                # Как вы видете там очень много изображений разного размера.
                # Возьмем изображение в самом лучшем качества.
                photos = sorted(photo['sizes'], key=lambda a: a['height'], reverse=True)
                # Отсортируем по размеру
                best_photo = photos[0]
                best_photo_url = best_photo['url']
                img = io.imread(best_photo_url)  # skimage умеет получать изображения по url

                #ввел ли пользователь число кластеров? Если да, то сохраняем
                max_clusters = 15
                min_clusters = 2

                сlusters=8
                user_clusters = re.findall(r'colors=(\d+)', text)

                text_answer_kmeans = 'Готово! Тут {} цветов.'.format(сlusters)
                if len(user_clusters) > 0:
                    user_clusters = int(user_clusters[0])
                    if ((user_clusters > min_clusters-1) and (user_clusters < max_clusters+1)):
                        сlusters = user_clusters
                        text_answer_kmeans = 'Nice! Держи! Тут {} цветов.'.format(сlusters)
                    else:
                        text_answer_kmeans = 'Допустимый диапазон цветов то {} до {}, сделал по дефолту. \n\n{}'.format(min_clusters, max_clusters, text_example )

                #преобразование картинки
                img_float_res = img_as_float(img).reshape(-1, 3)
                clf = KMeans(n_clusters=сlusters)
                clf.fit(img_float_res)
                segmented_image = clf.cluster_centers_[clf.labels_]
                segmented_image = segmented_image.reshape(img.shape)
                io.imsave("test.png", segmented_image)
                #io.imsave("test.png", img)  # сохраним изображение как test.png

                uploaded_photos = uploader.photo_messages("./test.png")
                # Можно загрузить несколько изображений сразу.
                # Выглядит так же как и attachment которые мы получаем в сообщении
                uploaded_photo = uploaded_photos[0]
                # Но сейчас у нас только одно.

                answer_with_img = {
                    'peer_id': peer_id,
                    'random_id': random.randint(0, 100000),
                }
                photo_attachment = f'photo{uploaded_photo["owner_id"]}_{uploaded_photo["id"]}'
                # <type><owner_id>_<media_id> Так должны выглядить вложенные изображения.
                # Например photo100172_166443618
                # Подробнее в https://vk.com/dev/messages.send

                # Добавим изображение к ответу
                answer_with_img.update({'attachment': photo_attachment})
                vk_session.method('messages.send', answer_with_img)
                # Можно отвечать и с текстом. Но обязательно в сообщении должен быть или текст или вложение
                print(answer_with_img)
                print()

            if len(text) > 0:
                # Ответим пользователю
                answer = {
                    'peer_id': peer_id,
                    # peer_id - ID кому отвечаем. Подробнее смотрите в документации. Нам сейчас и этого достаточно.
                    'random_id': random.randint(0, 100000),
                    # random_id - уникальный (в привязке к API_ID и ID отправителя) идентификатор,
                    # предназначенный для предотвращения повторной отправки одинакового сообщения.
                    # Сохраняется вместе с сообщением и доступен в истории сообщений.
                    # Заданный random_id используется для проверки уникальности за всю историю сообщений,
                    # поэтому используйте большой диапазон (до int64).
                }
                # Добавим текст к ответу
                text_default_dict = {
                    1: 'Ты много от меня хочешь!',
                    2: 'Мда...',
                    3: 'Ну и что тут не понятного ?!?',
                    4: '',
                    5: 'Давай еще раз!'
                }
                text_default = text_default_dict[random.randrange(1, 5, 1)]

                if flag_first_message:
                    flag_first_message = False
                    text_default = "Привет, я знаю KMeans! Короче, я могу преобразовать твою картинку в заданное количество цветов!"

                if len(text_answer_kmeans) > 0:
                    text_answer = text_answer_kmeans
                else:
                    text_answer = text_default + '\n\n' + text_example

                answer.update({'message': text_answer})
                vk_session.method('messages.send', answer)  # Отправляет сообщение
                # https://vk.com/dev/messages.send документация
                # Там еще есть очень много всего. Например, вместо peer_id можно оправлять user_id.
                print(answer)
                print()

# Это всего лишь пример, а не идеальный код.
# Как вы видите vk_api не очень удобное.
# И многие его части можно завернуть в классы и методы для удобства.

if __name__ == '__main__':
    while True:
        try:  # Чтоб не падало
            print("(RE)START")
            main()
        except Exception as err:
            full_stack_trace = traceback.format_exc()
            # Возвращяет всю ошибку. Иначе написало бы только последную строку
            print("BLIN {}".format(full_stack_trace))
