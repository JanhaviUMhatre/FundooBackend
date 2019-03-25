"""
******************************************************************************
* Purpose:  APIs (Register,Login,uploadImage,AddNote,DeleteNote,...).
*
* @author:  Pushkar Ishware
* @version: 3.7
* @since:   11-3-2018
*
******************************************************************************
"""
import base64
import io
import os

import botocore
from PIL.Image import isImageType

from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, HTTP_HEADER_ENCODING
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import CreateAPIView, UpdateAPIView, DestroyAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .ModelServices import GetNotes
# from .services import redis_info
from .CustomDecorator import custom_login_required
from .tokens import account_activation_token
from django.core.mail import EmailMessage
from django.http import HttpResponse, request
from django.contrib.auth import get_user_model, authenticate, login
import jwt
import json
from django.contrib.auth.models import User
import re
from django.http import JsonResponse
from PIL import Image
import boto3
from .serializers import registrationSerializer
# , LoginSerializer, NoteSerializer, LabelSerializer, MapLabelSerializer
from django.views import View
from .models import Note, Label, Map_Label
from .LoginSerializer import LoginSerializer
from .NoteSerializer import NoteSerializer
from .LabelSerializer import LabelSerializer
from .MapLabelSerializer import MapLabelSerializer

User = get_user_model()


def jwt_tok(request):
    uid = request.META['HTTP_AUTHORIZATION']

    print('from a header---------------------------', uid)
    print("uid -s ---", uid)
    userdata = jwt.decode(uid, "Cypher", algorithm='HS256')
    uname = userdata['username']
    valid = User.objects.get(username=uname)
    print(valid, "validation given token")
    if valid:
        return uname
    else:
        return "invalid entry"


def activate(request, uidb64, token):
    """ this is email activation method for checking given email is valid or not. """

    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)  # gets the username
        print('above if', user)
        if user and account_activation_token.check_token(user, token):
            user.is_active = True
            user.save()
            json_data = {
                "success": True,
                "message": "Successfully registered Go to login page"
            }
            return HttpResponse(json_data)
        else:
            return HttpResponse('Activation link is invalid!')
    except(TypeError, ValueError, User.DoesNotExist):
        return HttpResponse('Something bad happened')


from dotenv import load_dotenv


class RestRegistration(CreateAPIView):
    """ Registration API """

    serializer_class = registrationSerializer

    def post(self, request, *args, **kwargs):
        res = {"message": "something bad happened",
               "data": {},
               "success": False}
        print(request.data)
        username = request.data['username']
        email = request.data['email']
        password = request.data['password1']
        if username and email and password is not "":
            user = User.objects.create_user(username=username, email=email, password=password)
            user.is_active = False
            user.save()

            message = render_to_string('acc_active_email.html', {
                'user': user,
                'domain': 'http://127.0.0.1:8000',
                'domain1': os.getenv("DOMAIN"),
                'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                'token': account_activation_token.make_token(user),
            })
            mail_subject = 'Activate your account...'
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            res['message'] = "registered Successfully...Please activate your Account"
            res['success'] = True
            return Response(res)
        else:
            return Response(res)


from rest_framework.authtoken.models import Token


# @require_POST
class RestLogin(CreateAPIView):
    """ Login API """

    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        res = {"message": "something bad happened",
               "data": {},
               "success": False,
               "user_id": {}}
        print(request.data)
        try:
            username = request.data['username']
            if username is None:
                raise Exception("Username is required")
            password = request.data['password']
            if password is None:
                raise Exception("password is required")
            user = authenticate(username=username, password=password)
            print('user-->', user)

            if user:
                if user.is_active:
                    # login(request, user)
                    # user_id = request.user
                    payload = {'username': username, 'password': password}
                    # token = jwt.encode(payload, "secret_key", algorithm='HS256').decode('utf-8')
                    jwt_token = {
                        'token': jwt.encode(payload, os.getenv("SIGNATURE"), algorithm='HS256').decode('utf-8')
                    }
                    print(jwt_token)
                    token = jwt_token['token']
                    res['message'] = "Logged in Successfully"
                    res['data'] = {"token": token}
                    res['success'] = True
                    # redis_token = redis_info.token_set('token', res['data'])
                    # print("redis-----", redis_token)
                    return Response(res)
                else:
                    return Response(res)
            if user is None:
                return Response(res)
        except Exception as e:
            print(e)
            return Response(res)


class AddNote(CreateAPIView):
    """Add Notes API"""

    serializer_class = NoteSerializer

    @method_decorator(custom_login_required)
    def post(self, request, *args, **kwargs):
        uname = request.user_id
        print(uname, "    from add notes")
        try:
            res = {
                'message': 'Something bad happened',
                'success': False
            }
            # uname = jwt_tok(request)
            uid = User.objects.get(username=uname).pk
            print(uid)
            serializer = NoteSerializer(data=request.data)

            if request.data['title'] and request.data['description'] is None:
                raise Exception("title and description required ")

            print("title-------", request.data['title'])

            if serializer.is_valid():
                # serializer.user_id = uid
                serializer.save(user_id=uid)
                res['message'] = "note added"
                res['success'] = True
                return Response(res)
            return Response(res)
        except Exception as e:
            print(res, e)


from itertools import chain


class ShowNotes(View):
    """Show notes API"""

    @method_decorator(custom_login_required)
    def get(self, request):
        uname = request.user_id
        print("------------------authUSER-----", uname)
        global note_data
        res = {
            'message': 'Something bad happened',
            'data': {},
            'label': {},
            'success': False
        }
        try:
            # user_id=uid
            uid = User.objects.get(username=uname).pk
            print("user id from username-------", uid)
            note_data = Note.objects.filter(user_id=uid).values('id', 'title', 'description', 'is_archived', 'reminder',
                                                                'user', 'color', 'is_pinned', 'is_deleted', 'label',
                                                                'collaborate')
            data_list = []
            for i in note_data:
                data_list.append(i)
            note_json = json.dumps(data_list)

            # note_json = GetNotes(uid)

            # item = Note.collaborate.through.objects.filter(user_id=uid).values()
            # print(item,'collaborators')

            # collab = Note.collaborate.through.objects.filter(user_id=uid)
            #
            # print('col--------------------',collab)

            # Collaborated Notes of this user

            items = Note.collaborate.through.objects.filter(user_id=uid).values()
            print(items, 'itemmmmm from collab')
            names = []
            for i in items:
                j = User.objects.get(id=i['user_id'])
                # print(j.username)
                names.append(str(j))
            print('names---------', names)

            collab = []
            for i in items:
                collab.append(i['note_id'])
            # print('collab note id',collab)

            collab_notes = Note.objects.filter(id__in=collab).values('id', 'title', 'description', 'is_archived',
                                                                     'reminder',
                                                                     'user', 'color', 'is_pinned', 'is_deleted',
                                                                     'label',
                                                                     'collaborate')

            collab_json = []
            for i in collab_notes:
                collab_json.append(i)
            cj = json.dumps(collab_json)

            result_list = list(chain(data_list, collab_json))
            # print(result_list)
            result_json = json.dumps(result_list)
            # end of collaborator

            res['message'] = "Showing data."
            res['data'] = note_json

            res['success'] = True
            # print(res)
            j = json.dumps(res)

            # return HttpResponse(data1['label'])
            print('------------------------------end of show api-----------------')
            return HttpResponse(result_json)

        except Exception as e:
            print(res, e)


class UpdateNote(UpdateAPIView):
    """Update Notes API"""

    serializer_class = NoteSerializer
    queryset = Note.objects.all()

    @method_decorator(custom_login_required)
    def post(self, request, *args, **kwargs):
        try:
            res = {
                'message': 'Something bad happened',
                'success': False
            }
            queryset = Note.objects.get(pk=request.data['id'])

            item = Note.objects.get(pk=request.data['id'])
            print(item)
            print(item.id)
            title = request.data['title']
            des = request.data['description']
            color = request.data['color']
            remainder = request.data['reminder']

            item.title = title
            item.description = des
            item.color = color
            item.reminder = remainder

            item.save()
            # UpdateNote()

            res['message'] = "Update Successfully"
            res['success'] = True

            return Response(res)
            # return HttpResponse(res)
        except Exception as e:
            print(res, e)


class DeleteNote(UpdateAPIView):
    """Delete Notes API"""

    serializer_class = NoteSerializer
    queryset = Note.objects.all()

    @method_decorator(custom_login_required)
    def post(self, request, *args, **kwargs):
        uname = request.user_id
        print(uname)
        try:
            res = {
                'message': 'Something bad happened',
                'success': False
            }
            item = Note.objects.get(pk=request.data['id'])
            print(item)
            print(item.id)
            delete = request.data['is_deleted']
            item.is_deleted = delete
            item.save()
            res['message'] = "Delete Successfully"
            res['success'] = True
            return Response(res)
        except Exception as e:
            print(res, e)


class PinUnpinNote(UpdateAPIView):
    """ PinUnpin Notes API """

    serializer_class = NoteSerializer
    queryset = Note.objects.all()

    @method_decorator(custom_login_required)
    def post(self, request, *args, **kwargs):
        try:
            res = {
                'message': 'Something bad happened',
                'success': False
            }
            item = Note.objects.get(pk=request.data['id'])
            print(item)
            print(item.id)
            pin = request.data['is_pinned']
            item.is_pinned = pin
            item.save()
            res['message'] = "Pinunpin Successfully"
            res['success'] = True
            return Response(res)
        except Exception as e:
            print(res, e)


class Reminder(View):
    """Reminder notes API"""

    @method_decorator(custom_login_required)
    def get(self, request):

        global note_data
        uname = request.user_id

        uid = uid = User.objects.get(username=uname).pk
        res = {
            'message': 'Something bad happened',
            'data': {},
            'success': False
        }
        try:
            note_data = Note.objects.filter(user_id=uid).values('id', 'title', 'description', 'reminder', )
            rem_notes = []
            for i in note_data:
                if i['reminder']:
                    rem_notes.append(i)
            print(rem_notes)
            z = json.dumps(rem_notes)
            return HttpResponse(z)
        except Exception as e:
            print(res, e)


class ArchiveNote(UpdateAPIView):
    """ArchiveNotes Notes API"""

    serializer_class = NoteSerializer
    queryset = Note.objects.all()

    @method_decorator(custom_login_required)
    def post(self, request, *args, **kwargs):
        try:
            res = {
                'message': 'Something bad happened',
                'success': False
            }
            queryset = Note.objects.get(pk=request.data['id'])
            item = Note.objects.get(pk=request.data['id'])
            print(item)
            print(item.id)
            archive = request.data['is_archived']
            item.is_archived = archive
            item.save()
            res['message'] = "Archived Successfully"
            res['success'] = True
            return Response(res)
        except Exception as e:
            print(res, e)


class CreateLabel(CreateAPIView):
    """Create Labels API"""

    serializer_class = LabelSerializer

    @method_decorator(custom_login_required)
    def post(self, request, *args, **kwargs):
        uname = request.user_id
        print('inside post')
        try:
            res = {
                'message': 'Something bad happened',
                'success': False
            }
            print(uname, "-***************************")
            uid = User.objects.get(username=uname).pk
            print(uid)
            print(request.data)
            # note_id = Note.objects.get(pk=request.data['id'])

            serializer = LabelSerializer(data=request.data)
            label = request.data['label_name']
            # print(serializer)
            if request.data['label_name'] is "":
                raise Exception("label name required ")

            if serializer.is_valid():
                serializer.user_id = uid
                serializer.save(user_id=uid)
                res['message'] = "label added"
                res['success'] = True
                return JsonResponse(res)
            return JsonResponse(res)
        except Exception as e:
            print(res, e)


class Showlabels(View):
    """Show labels API"""

    @method_decorator(custom_login_required)
    def get(self, request):
        global note_data
        uname = jwt_tok(request)
        uname = jwt_tok(request)
        # print(uname,"------------------------------------")

        res = {
            'message': 'Something bad happened',
            'data': {},
            'success': False
        }
        try:
            # user_id=uid
            uid = User.objects.get(username=uname).pk
            print("user id from username-------", uid)
            note_data = Label.objects.filter(user_id=uid).values('id', 'label_name', 'user')
            print(type(note_data))

            data_list = []
            for i in note_data:
                data_list.append(i)
            print(data_list)
            z = json.dumps(data_list)

            # print("zzzzzzzz type", type(z))
            # print(z)
            res['message'] = "Showing data."
            res['data'] = z
            res['success'] = True
            return HttpResponse(z)

        except Exception as e:
            print(res, e)


class DeleteLabel(DestroyAPIView):
    """Delete labels API"""

    @method_decorator(custom_login_required)
    def delete(self, request, pk):
        print("inside Delete")

        res = {
            'message': 'label Deleted',
            'data': {},
            'success': True
        }
        Label.objects.get(pk=pk).delete()
        return Response(res)


class MapLabel(CreateAPIView):
    """Map labels API"""

    serializer_class = MapLabelSerializer

    # serializer_class1 = NoteSerializer  # adding labels to Note Models

    @method_decorator(custom_login_required)
    def post(self, request, *args, **kwargs):
        uname = request.user_id
        print('inside post')
        res = {
            'message': 'Something bad happened',
            'data': {},
            'success': False
        }
        if User.objects.get(username=uname).pk:
            uid = User.objects.get(username=uname).pk
            card = Note.objects.get(pk=request.data['id'])
            cid = card.id
            label = Label.objects.get(pk=request.data['label_id'])
            print("from map label -------", label)
            lid = label.id
            mapping = Map_Label.objects.create(label_id=Label.objects.get(id=lid),
                                               user=User.objects.get(id=uid),
                                               note=Note.objects.get(id=cid),
                                               map_label_name=Label.objects.get(label_name=label))
            res['message'] = 'label added'
            res['success'] = True
            res['data'] = {"label_id": lid}
            return Response(res)


class GetMapLabels(View):
    """Show Map labels API"""

    @method_decorator(custom_login_required)
    def get(self, request):
        uname = request.user_id
        # uname = jwt_tok(request)
        # uname = "pushkar111"
        res = {
            'message': 'Something bad happened',
            'data': {},
            'success': False
        }
        try:
            uid = User.objects.get(username=uname).pk
            print("user id from username-------", uid)
            note_data = Map_Label.objects.filter(user_id=uid).values('id', 'user_id',
                                                                     'map_label_name',
                                                                     'note_id')
            data_list = []
            for i in note_data:
                data_list.append(i)
            print(data_list)
            z = json.dumps(data_list)
            print("zzzzzzzz type", type(z))
            print(z)
            res['message'] = "Showing data."
            res['data'] = z
            res['success'] = True
            return HttpResponse(z)
        except Exception as e:
            print(res, e)


class RemoveMapLabel(DestroyAPIView):
    """Remove labels API"""

    @method_decorator(custom_login_required)
    def delete(self, request, pk):
        print("inside Delete")

        res = {
            'message': 'label removed successfully',
            'data': {},
            'success': True
        }
        Map_Label.objects.get(pk=pk).delete()
        return Response(res)


class AddCollaborator(CreateAPIView):
    """Add Collaborator API"""

    serializer_class = NoteSerializer

    @method_decorator(custom_login_required)
    def post(self, request, *args, **kwargs):
        print("inside post")
        res = {
            'message': 'collaborated successfully',
            'data': {},
            'success': True
        }
        card_id = request.data['id']
        print(card_id, "from frontend using method")

        # card_details = Note.objects.filter(id=card_id).values()
        card_details = Note.objects.get(id=card_id)

        print(card_details, "of given card..................")

        title = card_details.title
        print(title)
        description = card_details.description
        print(description)
        color = card_details.color
        print(color)
        new_user = request.data['new_username']
        print("add collab name--------------------", new_user)
        uid = User.objects.get(username=new_user).pk
        print(uid)
        card_details.save()
        return Response(res)


# class DeleteCollaborator(DestroyAPIView):
#     """Delete Collaborator API"""
#
#     @method_decorator(custom_login_required)
#     def delete(self, request, pk):
#         print("inside Delete")
#
#         res = {
#             'message': 'Collaborator Deleted',
#             'data': {},
#             'success': True
#         }
#         # items = Note.collaborate.through.objects.filter(user_id=pk,note_id=noteid).values()
#         # print(items, 'itemmmmm from collab')
#         # Label.objects.get(pk=pk).delete()
#         return Response(res)


class RestProfile(CreateAPIView):
    """Add Collaborator API"""

    serializer_class = NoteSerializer

    @method_decorator(custom_login_required)
    def post(self, request, *args, **kwargs):
        print("inside post")
        res = {
            'message': 'Image Uploaded',
            'data': {},
            'success': True
        }
        uname = request.user_id
        pic = request.data['profile1']

        # working code
        pic = pic[22:]
        image = base64.urlsafe_b64decode(pic)
        buf = io.BytesIO(image)
        img = Image.open(buf, 'r').convert("RGB")
        img.show()
        out_img = io.BytesIO()
        s3 = boto3.client('s3')
        # out_img = BytesIO()
        img.save(out_img, format="jpeg")
        img.seek(0)
        print('------------', img)
        img3 = Image.open(out_img)
        print('img 3-----', img3)
        print(img3.size)
        img3.save(os.path.join('/home/admin1/Desktop/' + str(uname) + '.jpeg'), 'JPEG')
        file = open('/home/admin1/Desktop/' + str(uname) + '.jpeg', 'rb')
        s3.upload_fileobj(file, 'bucketprofile', Key=str(uname) + ".jpeg")
        z = json.dumps(res)
        return HttpResponse(z)


class ImageUrl(View):

    @method_decorator(custom_login_required)
    def get(self, request):
        uname = request.user_id
        print("------------------inside imgURL get url-----", uname)

        link = "https://s3.ap-south-1.amazonaws.com/bucketprofile/" + str(uname) + ".jpeg"

        s3 = boto3.resource('s3')
        try:
            s3.Object('bucketprofile', str(uname) + ".jpeg").load()
            print("found")
            res = {"data": link, "username": str(uname)}
            res_json = json.dumps(res)
            return HttpResponse(res_json)

        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                print("not found")
                link = "https://s3.ap-south-1.amazonaws.com/bucketprofile/Default_Photo.jpeg"
                res = {"data": link, "username": str(uname)}
                res_json = json.dumps(res)
                return HttpResponse(res_json)
