# -*- coding: utf-8 -*-
from flask_nemo.plugin import PluginPrototype
from flask import jsonify,request
import MyCapytain.common.reference

class AnnotationsApiPlugin(PluginPrototype):
    """AnnotationsApiPlugin adds routes to Nemo 
    from which annotations can be retrieved
    :param queryinterface: QueryInterface to use to retrieve annotations
    :type queryinterface: QueryInterface
    """

    ROUTES =  [
        ("/annotations/api/target/<target_urn>", "r_annotations_by_target", ["GET"]),
        ("/annotations/api/resources/<uri>", "r_annotation_get", ["GET"])
    ]

    def __init__(self,queryinterface,*args,**kwargs):
        super(AnnotationsApiPlugin,self).__init__(*args,**kwargs)
        self.__queryinterface__ = queryinterface

    #TODO we should have a response at the base of annotations/api that returns link types and link relations
    # showing the next level of options 
    
    def r_annotations_by_target(self, target_urn):
        """ Route to retrieve annotations by target 
        :param target_urn: The CTS URN for which to retrieve annotations  
        :type target_urn: str
        :return: a JSON string containing count and list of resources
        :rtype: {str: Any}
        """
   
        try:
            urn = MyCapytain.common.reference.URN(target_urn)
        except ValueError:
            return "invalid urn", 400
       
        wildcard = request.args.get("wildcard", ".", type=str)
        include = request.args.get("include")
        exclude = request.args.get("exclude")
        limit = request.args.get("limit",None,type=int)
        start = request.args.get("start",1,type=int)
        expand = request.args.get("expand",False,type=bool)
        count,annotations = self.__queryinterface__.getAnnotations(target_urn, wildcard=wildcard, include=include, exclude=exclude, limit=limit, start=start, expand=expand) 
        mapped = {}
        response = { 'count':count }
        for a in annotations:
            slug = a.slug
            if not mapped[slug]:
                 mapped[slug] = []
            mapped[slug].append(a)
        response['annotations'] = mapped
        return jsonify(response)

    def r_annotation_get(self, uri):
        """ Route to retrieve contents of an annotation resource
        :param uri: The uri of the annotation resource
        :type uri: str
        :return: annotation contents
        :rtype: {str: Any}
        """
        annotation = self.__queryinterface__.getResource(uri)
        if not annotation:
            return "invalid resource uri", 404
        # TODO this should inspect the annotation content
        # set appropriate Content-Type headers
        # and return the actual content
        return jsonify(annotation)
