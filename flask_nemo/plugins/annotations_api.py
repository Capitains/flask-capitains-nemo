# -*- coding: utf-8 -*-
from flask_nemo.plugin import PluginPrototype
from flask import jsonify, request, url_for, Response
import MyCapytain.common.reference


class AnnotationsApiPlugin(PluginPrototype):
    """AnnotationsApiPlugin adds routes to Nemo from which annotations can be retrieved

    This plugins contains two routes only registered at

    - /api/annotations/?target=<URN Target> which is the collection in which to search
    - /api/annotations/<SHA Identifier of the annotation> is the annotation object
    - /api/annotations/<SHA Identifier of the annotation>/body is the proxy for the annotation body

    The response are conform to https://www.w3.org/TR/annotation-model/#annotation-collection

    :param queryinterface: QueryInterface to use to retrieve annotations
    :type queryinterface: QueryInterface

    """

    JSONLD_CONTEXT = {
        "": "http://www.w3.org/ns/anno.jsonld",
        "dc": "http://purl.org/dc/terms/",
        "owl": "http://www.w3.org/2002/07/owl#",
        "nemo": "https://capitains.github.io/flask-capitains-nemo/ontology/#"
    }
    ROUTES = [
        ("/api/annotations", "r_annotations", ["GET"]),
        ("/api/annotations/<sha>", "r_annotation", ["GET"]),
        ("/api/annotations/<sha>/body", "r_annotation_body", ["GET"])
    ]

    def __init__(self, queryinterface, *args, **kwargs):
        super(AnnotationsApiPlugin, self).__init__(*args, **kwargs)
        self.__queryinterface__ = queryinterface

    # TODO we should have a response at the base of annotations/api that returns link types and link relations
    # showing the next level of options 
    
    def r_annotations(self):
        """ Route to retrieve annotations by target

        :param target_urn: The CTS URN for which to retrieve annotations  
        :type target_urn: str
        :return: a JSON string containing count and list of resources
        :rtype: {str: Any}
        """

        target = request.args.get("target", None)
        wildcard = request.args.get("wildcard", ".", type=str)
        include = request.args.get("include")
        exclude = request.args.get("exclude")
        limit = request.args.get("limit", None, type=int)
        start = request.args.get("start", 1, type=int)
        expand = request.args.get("expand", False, type=bool)

        if target:

            try:
                urn = MyCapytain.common.reference.URN(target)
            except ValueError:
                return "invalid urn", 400

            count, annotations = self.__queryinterface__.getAnnotations(urn, wildcard=wildcard, include=include,
                                                                        exclude=exclude, limit=limit, start=start,
                                                                        expand=expand)
        else:
            #  Note that this implementation is not done for too much annotations
            #  because we do not implement pagination here
            count, annotations = self.__queryinterface__.getAnnotations(None, limit=limit, start=start, expand=expand)
        mapped = []
        response = {
            "@context": type(self).JSONLD_CONTEXT,
            "id": url_for(".r_annotations", start=start, limit=limit),
            "type": "AnnotationCollection",
            "startIndex": start,
            "items": [
            ],
            "total": count
        }
        for a in annotations:
            mapped.append({
                "id": url_for(".r_annotation", sha=a.sha),
                "body": url_for(".r_annotation_body", sha=a.sha),
                "type": "Annotation",
                "target": a.target.to_json(),
                "dc:type": a.type_uri,
                "owl:sameAs": [a.uri],
                "nemo:slug": a.slug
            })
        response["items"] = mapped
        response = jsonify(response)
        return response

    def r_annotation(self, sha):
        """ Route to retrieve contents of an annotation resource

        :param uri: The uri of the annotation resource
        :type uri: str
        :return: annotation contents
        :rtype: {str: Any}
        """
        annotation = self.__queryinterface__.getResource(sha)
        if not annotation:
            return "invalid resource uri", 404
        response = {
            "@context": type(self).JSONLD_CONTEXT,
            "id": url_for(".r_annotation", sha=annotation.sha),
            "body": url_for(".r_annotation_body", sha=annotation.sha),
            "type": "Annotation",
            "target": annotation.target.to_json(),
            "owl:sameAs": [annotation.uri],
            "dc:type": annotation.type_uri,
            "nemo:slug": annotation.slug
        }
        return jsonify(response)

    def r_annotation_body(self, sha):
        """ Route to retrieve contents of an annotation resource

        :param uri: The uri of the annotation resource
        :type uri: str
        :return: annotation contents
        :rtype: {str: Any}
        """
        annotation = self.__queryinterface__.getResource(sha)
        if not annotation:
            return "invalid resource uri", 404
        # TODO this should inspect the annotation content
        # set appropriate Content-Type headers
        # and return the actual content
        content = annotation.read()
        if isinstance(content, Response):
            return content
        headers = {"Content-Type": annotation.mimetype}
        return Response(content, headers=headers)
