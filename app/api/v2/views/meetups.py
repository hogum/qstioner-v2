from flask_restful import Resource, reqparse, inputs
from flasgger import swag_from
from flask import current_app as app
import werkzeug

import os
import datetime
import string
import random

from ..models.meetups import MeetUpModel
from ..utils.auth import admin_required, auth_required
from ..utils.helpers import validate_date
from ..database.queries import (
    GET_ALL_MEETUPS, DELETE_MEETUP, GET_TAGGED_MEETUPS, UPDATE_MEETUP)


class Meetups(Resource):
    """
        This resource allows an admin user to create a meetup.
        It also makes it possible for any user to fetch all existing meetups
    """
    @auth_required
    @admin_required
    @swag_from('docs/meetup_post.yml')
    def post(this_user, self):
        parser = reqparse.RequestParser(trim=True, bundle_errors=True)
        parser.add_argument('topic', required=True,
                            type=inputs.regex('^[A-Za-z0-9_ ?/.,"\\\':;]+$'),
                            help="Topic is empty or has invalid characters")
        parser.add_argument(
            'happeningOn', type=validate_date,
            default=datetime.datetime.utcnow().isoformat(), required=True)
        parser.add_argument('tags',
                            type=inputs.regex('^[A-Za-z0-9_ -/]+$'),
                            help="Tag is empty or has invalid characters",
                            action='append')
        parser.add_argument('location', required=True,
                            type=inputs.regex('^[A-Za-z0-9_ ?/.,"\\\':;]+$'),
                            help="Location is empty or has invalid characters")
        parser.add_argument('images', type=str, action='append')

        args = parser.parse_args(strict=True)

        # Ensure a meetup isn't created with same data twice

        new_meetup = MeetUpModel(**args)

        if MeetUpModel.verify_unique(new_meetup):
            return {
                "status": 409,
                "message": "Relax, Meetup already created"
            }, 409

        data = new_meetup.save()

        return {
            "status": 201,
            "data": [MeetUpModel.zipToDict(keys, data, single=True)]
        }, 201


class MeetUp(Resource):
    """
        This resource fetches all existing meetup records
    """
    @auth_required
    @swag_from('docs/meetups_get.yml')
    def get(this_user, self):

        data = MeetUpModel.get_all(GET_ALL_MEETUPS)

        if data:
            data = MeetUpModel.zipToDict(keys, data)
        return {
            "status": 200,
            "data": data
        }, 200


class MeetUpItem(Resource):
    """
        Searches for a meetup by its id
        and returns a matching record.
    """
    @auth_required
    @swag_from('docs/meetup_get.yml')
    def get(this_user, self, id):

        if not MeetUpModel.get_by_id(id):
            return {
                "status": 404,
                "error": "Meetup non-existent"
            }, 404
        return {
            "status": 200,
            "data": [MeetUpModel.get_by_id(id)]
        }, 200

    @auth_required
    @swag_from('docs/meetup_delete.yml')
    def delete(this_user, self, id):
        """
            Clears a specified meetup from the meetups records.
        """
        meetup = MeetUpModel.get_by_id(id, obj=True)
        if not meetup:
            return {
                "status": 404,
                "error": "Meetup non-existent"
            }, 404
        else:
            data = meetup.delete(DELETE_MEETUP, (id,))
            print(data)
            if not data:
                return {
                    "status": 409,
                    "message": f"Meetup {id} has relations." +
                    "Delete not Possible"
                }, 409
        return {
            "status": 200,
            "message": "MeetUp deleted",
            "item": repr(meetup)
        }, 200

    @auth_required
    @admin_required
    @swag_from('docs/meetups_put.yml')
    def put(this_user, self, id):
        """
            Updates an existing meetup with details passed in
            by user
        """
        parser = reqparse.RequestParser(trim=True, bundle_errors=True)
        parser.add_argument('topic',
                            type=inputs.regex('^[A-Za-z0-9_ ?/.,"\\\':;]+$'),
                            help="Topic is empty or has invalid characters")
        parser.add_argument(
            'happeningOn', type=validate_date,
            default=datetime.datetime.utcnow().isoformat())
        parser.add_argument('tags', action='append',
                            type=inputs.regex('^[A-Za-z0-9_ /"\\\'-]+$'),
                            help="Tag is empty or has invalid characters")
        parser.add_argument('location',
                            type=inputs.regex('^[A-Za-z0-9_ ,:;?/.,"\\\'-]+$'),
                            help="Location is empty or has invalid characters")
        parser.add_argument('images', type=str, action='append')

        args = parser.parse_args(strict=True)

        meetup = MeetUpModel.get_by_id(id, obj=True)
        if not meetup:
            return {
                "status": 404,
                "error": f"Meetup of ID {id} non-existent"
            }, 404

        data = meetup.dictify()

        data.update({key: value for key, value
                     in args.items() if value})
        new_data = dict(
            topic=data.get('topic'),
            happeningOn=data.get('happeningOn'),
            location=data.get('location'))
        new_data.update({'id': id})

        meetup.update(UPDATE_MEETUP, tuple(new_data.values()))

        return {
            "status": 200,
            "message": "Meetup updated",
            "data": [MeetUpModel.get_by_id(id)]
        }, 200


class MeetupImage(Resource):
    """
        Allows uploading of image files to exisiting meetups
    """
    decorators = [auth_required]

    @swag_from('docs/meetup_image_post.yml')
    def post(this_user, self, id):
        """
            Uploads an image to the meetup whose ID
            matches the ID specified in the PATH
        """
        parser = reqparse.RequestParser(trim=True, bundle_errors=True)

        parser.add_argument('image', type=werkzeug.datastructures.FileStorage,
                            location='files')
        args = parser.parse_args(strict=True)

        image = args.get('image')

        # ! err Doesn't handle missing paths
        """if not image:
            return {
                "status": 400,
                "error": "Image path is Empty. Specify an image"
            }, 400
        """

        meetup = MeetUpModel.get_by_id(id, obj=True)

        if not meetup:
            return {
                "status": 404,
                "message": f"Meetup of ID {id} non-existent"
            }, 404

        # Set random file name
        random_name_part = ''.join(random.choices(
            string.ascii_lowercase + string.digits, k=30))
        image_name = 'meetup' + str(id) + random_name_part + '.png'

        file_path = os.path.join(app.config.get('UPLOAD_DIR'),
                                 image_name)

        image.save(file_path)
        meetup.add_image(file_path, id)

        return {
            "status": 200,
            "message": "Upload Successful",
        }, 200


keys = ["id", "topic", "images", "location", "happening_on",
        "tags"]


class MeetUpTags(Resource):
    """
        This resource allows an admin user to associate
        tags in helping in identification of meetups
    """
    @auth_required
    @admin_required
    @swag_from('docs/meetup_tags_post.yml')
    def post(this_user, self, meetup_id, tag):
        """
            Posts a tag to a meetup record that matches
            the given ID
        """

        meetup = MeetUpModel.get_by_id(meetup_id, obj=True)

        if not meetup:
            response = "That meetup seems \
            missing" + f'Meetup of ID {meetup_id} not in existence yet'
            return {
                "status": 404,
                "message": response
            }, 404

        data = meetup.add_array_tag(tag, meetup_id)
        print(data, "\n\n\n", "tags")

        return {
            "status": 200,
            "message": f"Tag {tag} associated with meetup of ID {meetup_id}"
        }, 200


class MeetUpTag(Resource):

    """
        Allows users to see records associated with certain tags.
    """
    @auth_required
    @swag_from('docs/meetup_tags_get.yml')
    def get(this_user, self, tag):
        """
        Fetches meetups that match a given tag and returns
        a response of these meetup records.
        """

        data = MeetUpModel.get_all(GET_TAGGED_MEETUPS, (tag,))

        if data:
            data = MeetUpModel.zipToDict(keys, data)
        return {
            "status": 200,
            "data": data
        }, 200
