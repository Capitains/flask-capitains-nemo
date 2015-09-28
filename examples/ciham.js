(function ($) {
      $.each(['show', 'hide'], function (i, ev) {
        var el = $.fn[ev];
        $.fn[ev] = function () {
          this.trigger(ev);
          return el.apply(this, arguments);
        };
      });
    })(jQuery);


$(document).ready(function() {

	$("ol, span").removeClass("norm");
	
	$("#fac").on("click", function() {
		that = $(this);
			$("ol, span").removeClass("norm");
			$(".orig , .abbr" ).show();
			$(".reg , .expan").hide();
			$("br").show();
		$(".btn-success").addClass("btn-default").removeClass("btn-success");
		that.addClass("btn-success").removeClass("btn-default");

	});
	

	$("#reg").on("click", function() {
		that = $(this);
			$("ol, span, div").addClass("norm");
			$(".orig , .abbr").hide();
			$(".reg , .expan").show();
			$("br").hide();
			//$(".metamark").removeClass("information-hr");
			//that.removeClass("information-hr");
		$(".btn-success").addClass("btn-default").removeClass("btn-success");
		that.addClass("btn-success").removeClass("btn-default");
	});

	$("#seeWitness").on("click", function() {
		that = $(this);
		$("#seeWitness li").toggleClass("wit");
	});

	


	$("sup a, .information-hr").tooltip();

	$(".orig , .abbr , .reg , .expan").on("show", function(e) {
		if($(this).is("span")) {
			//$(this).css("display", "inline-block");//
		}
 	});
});


