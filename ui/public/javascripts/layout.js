/*
Created By: James Shin
Date: 2017-11-15
*/
if(typeof(String.prototype.trim) === "undefined"){
  String.prototype.trim = function() 
  {
    return String(this).replace(/^\s+|\s+$/g, '');
  };
}
var en = {
  title : "Search Collective Agreements",
  helpBtn : "Help",
  tutorialBtn : "Tutorial",
  feedbackBtn : "Feedback",
  downloadBtn : "Download",
  resultsTxt : " Results Found"
};
var fr = {
  title : "Search Collective Agreements FR",
  helpBtn : "Aider",
  tutorialBtn : "Tutorial FR",
  feedbackBtn : "Feedback FR",
  downloadBtn : "Download FR",
  resultsTxt : " Results Found FR"
}
var tutMode = false;

function debounce(func, wait, immediate) {
  var timeout;
  return function() {
    var context = this, args = arguments;
    var later = function() {
      timeout = null;
      if (!immediate) func.apply(context, args);
    };
    var callNow = immediate && !timeout;
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
    if (callNow) func.apply(context, args);
  };
};

$(document).ready(function (){

  //Init
  $('#filter-div input').val('');

  function loadingAnimation(){
    $("#search-results").html('<div id="loading-container"><div class="lds-css"><div style="width:200px;height:200px;" class="lds-ripple"><div></div><div></div></div></div></div>');
  }

  //search event listener
  $("#search-bar").keyup(debounce(function(event){
    //When enter is pressed on search bar
    if(event.which == 13){
      if($("#auto-complete .auto-comp-active").length){
        $('#search-bar').val($("#auto-complete .auto-comp-active").text());
        socket.emit('autoCompleteSelected', {selectedId: $("#auto-complete .auto-comp-active").attr("data-uid")});
      }

      //Hide filter
      $('#filter-div').transition({opacity:0});
      $('#filter-btn').removeClass('active');

      $("#auto-complete").html("").css("border-top", "none");
      //If there are search results currently...
      if($("#search-results").html() != ''){
        $("#search-results").fadeOut(function (){
          //Loading Gif
          $(this).fadeIn();
          loadingAnimation();
          //Search for something
          var tempVar = "";
          if($("#filter-pdfname-input").val().length){
            tempArr = $("#filter-pdfname-input").val();
            for (var i = 0; i < tempArr.length; i++) {
              tempArr[i] = tempArr[i].replace('-','') + "a";
            };
            tempVar = ("'"+tempArr.join("','")+"'");
          }
          socket.emit('searchAttempt', {searchInput:$('#search-bar').val(), searchFilter:{pdfName:tempVar}});
        });
      }else{
        //Loading Gif
        loadingAnimation();
        //Search for something
        var tempVar = "";
        if($("#filter-pdfname-input").val().length){
          var tempVar = "";
          if($("#filter-pdfname-input").val().length){
            tempArr = $("#filter-pdfname-input").val();
            for (var i = 0; i < tempArr.length; i++) {
              tempArr[i] = tempArr[i].replace('-','') + "a";
            };
            tempVar = ("'"+tempArr.join("','")+"'");
          }
          //tempVar = $("#filter-pdfname-input").val().toString().replace('-','') + "a";
        }
        console.log(tempVar);
        socket.emit('searchAttempt', {searchInput:$('#search-bar').val(), searchFilter:{pdfName:tempVar}});
      }
    }else if(event.which == 40){
      //Down
      if($("#auto-complete .auto-comp-active").length != 0){
        //if list is not empty
        if($("#auto-complete .auto-comp-active").next().length){
          $("#auto-complete .auto-comp-active").removeClass('auto-comp-active').next().addClass('auto-comp-active');
        }
      }else{
        $("#auto-complete p").eq(0).addClass("auto-comp-active");
      }
    }else if(event.which == 38){
      //Up
      if($("#auto-complete .auto-comp-active").length != 0){
        //if list is not empty
        if($("#auto-complete .auto-comp-active").prev().length){
          $("#auto-complete .auto-comp-active").removeClass('auto-comp-active').prev().addClass('auto-comp-active');
        }else{
          $("#auto-complete .auto-comp-active").removeClass('auto-comp-active');
        }
        var tempInput = $("#search-bar").val();
        $("#search-bar").val("");
        $("#search-bar").val(tempInput);
      }
    }else if(event.which == 37 || event.which == 39 || event.which == 16 || event.which == 17 || event.which == 18 || event.which == 9){

    }else{
      //When search bar has text greater than 3 characters
      if($(this).val().length > 3){
        socket.emit('autoCompleteAttempt', {searchInput:$('#search-bar').val()});
      }else{
        $("#auto-complete").html("").css("border-top", "none");
      }
    }
  },50));

  //Filter button
  $('#filter-btn').click(function (){
    var currentState = false;
    if($(this).hasClass('active')){
      $(this).removeClass('active');
      currentState = false;
    }else{
      $(this).addClass('active');
      currentState = true;
    }
    //move svg.
    $.each($('#filter-btn svg').find('rect'), function (i, sel){
      if(currentState){
        $(sel).attr('x',0);
      }else{
        $(sel).attr('x',$(sel).data('x'));
      }
    });

    if(currentState){
      //show filter table
      $('#filter-div').width($('#search-bar-div').width());
      $('#filter-div').transition({opacity:1});
    }else{
      //hide filter
      $('#filter-div').transition({opacity:0});
      $('#filter-div input').val('');
      $("#search-filters").transition({opacity:0});
    }
  });

  //Search Filter Icon
  $("#filter-pdfname-input").chosen({width:"100%", placeholder_text_multiple:"Type in Agreement Number", no_results_text: "More Numbers Required"});
  $("#filter-pdfname").find('.chosen-search-input').keyup(function (event){
    if(event.which == 37 || event.which == 39 || event.which == 16 || event.which == 17 || event.which == 18 || event.which == 9 || event.which == 38 || event.which == 40 || event.which == 13){

    }else{
      if($(this).val().length > 3){
        socket.emit('pdfNameSearch', {searchInput:$(this).val()});
      }
    }
  });

/*
  $('#filter-pdfname-input').keyup(function (event){
    if($(this).val() == ''){
      $("#search-filters").transition({opacity:0});
    }
    if($("#search-filters").css('opacity') == 0){
      $("#search-filters").transition({opacity:1});
    }
    if(event.which == 13){
      var e = $.Event( "keyup", { which: 13 } );
      $("#search-bar").trigger(e);
    }else{
      $("#search-filters").text("Within "+$(this).val()+".pdf");
    }
  });
*/

  //French Translations
  $('#french-btn').click(function (){
    if($(this).attr("data-current") == 'en'){
      $(this).attr("data-current","fr");
      $(this).attr("data-tooltip","English");
      $(this).tooltip({delay: 50});
      $(this).transition({
        perspective: '100px',
        rotateX: '180deg',
        complete: function (){
          $('#french-btn').removeClass('teal').addClass('indigo').text("En");
        }
      }).transition({
        perspective: '100px',
        rotateX: '0deg'
      });
      $("#search-title").text(fr.title);
      //$("#help-btn").attr("data-tooltip",fr.helpBtn);
      $("#tutorial-btn").attr("data-tooltip",fr.tutorialBtn);
      //$("#feedback-btn").attr("data-tooltip",fr.feedbackBtn);
      $(".download-btns").each(function (){
        $(this).attr("data-tooltip",fr.downloadBtn);
      });
    }else{
      $(this).attr("data-current","en");
      $(this).attr("data-tooltip","Français");
      $(this).tooltip({delay: 50});
      $(this).transition({
        perspective: '100px',
        rotateY: '180deg',
        complete: function (){
          $('#french-btn').removeClass('indigo').addClass('teal').text("Fr");
        }
      }).transition({
        perspective: '100px',
        rotateY: '0deg'
      });

      $("#search-title").text(en.title);
      //$("#help-btn").attr("data-tooltip",en.helpBtn);
      $("#tutorial-btn").attr("data-tooltip",en.tutorialBtn);
      //$("#feedback-btn").attr("data-tooltip",en.feedbackBtn);
      $(".download-btns").each(function (){
        $(this).attr("data-tooltip",en.downloadBtn);
      });
    }

    //$("#help-btn-div a").tooltip({delay: 50});
    $(".download-btns").tooltip({delay: 0}).each(function (){
      $("#"+$(this).attr('data-tooltip-id')).css("margin-top", "16px").css("margin-left", "-8px");
    });
  });

  /*
  $("#help-btn").click(function (){
    $("#help-btn-div a").tooltip({delay: 50});
  });
  */
  //Tutorial
  $("#tutorial-btn").click(function (){
    tutMode = true;
    $(".tut1explain").css("display","block");
    $("#tutorial-div").show().transition({opacity:1});
    $("#tut1container").css("background-color","white").css('position', 'relative').css("z-index","101");
    $("#tut1explain1").transition({opacity:1, y:10, delay:1000});
    $("#tut1explain2").transition({opacity:1, y:10, delay:1500});
    $("#tut1explain3").transition({opacity:1, y:10, delay:2000});
    $("#tut1explain4").transition({opacity:1, y:10, delay:2500});
    $("#tut1explain5").transition({opacity:1, y:10, delay:3000});
    $("#tut1title").show();
    $("#tutorial-btn").hide();
    $("#close-btn-div").show();
  });

  $("#close-btn-div").click(function (){
    closeTutorial();
  });
  //Begining Init
  $("#search-bar").focus().val("");
  $("#search-results").css("top", ($(".container").height()+180) + "px");
});

function closeTutorial(){
  tutMode = false;
  $(".tut1explain").css("display","none");
  $("#tutorial-div").hide().transition({opacity:0, duration:0});
  $("#tut1explain1").transition({opacity:0, y:0, duration:0});
  $("#tut1explain2").transition({opacity:0, y:0, duration:0});
  $("#tut1explain3").transition({opacity:0, y:0, duration:0});
  $("#tut1explain4").transition({opacity:0, y:0, duration:0});
  $("#tut1explain5").transition({opacity:0, y:0, duration:0});

  $("#tutorial-btn").show();
  $("#close-btn-div").hide();
}
//Socket Io
socket.on('searchResults', function (data) {
  //hide loading gif
  $("#loading-container").fadeOut(function(){
    $(this).remove();
  });
  //Search Result Count
  /*
  if($('#french-btn').data("current") == 'en'){
    $("#search-results").append("<h4 id='search-results-count' style='opacity:0;'><b>"+data.data.length+"</b>"+en.resultsTxt+"</h4>");
  }else{
    $("#search-results").append("<h4 id='search-results-count' style='opacity:0;'><b>"+data.data.length+"</b>"+fr.resultsTxt+"</h4>");
  }
  $("#search-results-count").transition({opacity:1,delay:300});
  */

  var highlightResults = data.query.split(' ');
  var stopwords = [" ","a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any","are","aren't","as","at","be","because","been","before","being","below","between","both","but","by","can't","cannot","could","couldn't","did","didn't","do","does","doesn't","doing","don't","down","during","each","few","for","from","further","had","hadn't","has","hasn't","have","haven't","having","he","he'd","he'll","he's","her","here","here's","hers","herself","him","himself","his","how","how's","i","i'd","i'll","i'm","i've","if","in","into","is","isn't","it","it's","its","itself","let's","me","more","most","mustn't","my","myself","no","nor","not","of","off","on","once","only","or","other","ought","our","ours","ourselves","out","over","own","same","shan't","she","she'd","she'll","she's","should","shouldn't","so","some","such","than","that","that's","the","their","theirs","them","themselves","then","there","there's","these","they","they'd","they'll","they're","they've","this","those","through","to","too","under","until","up","very","was","wasn't","we","we'd","we'll","we're","we've","were","weren't","what","what's","when","when's","where","where's","which","while","who","who's","whom","why","why's","with","won't","would","wouldn't","you","you'd","you'll","you're","you've","your","yours","yourself","yourselves"];
  for(var i = highlightResults.length-1; i--;){
    if(highlightResults[i] == '' || highlightResults == " "){
      highlightResults.splice(i, 1);
    }else{
      var tempComp = highlightResults[i].toLowerCase();
      if(stopwords.indexOf(tempComp) != -1){
        highlightResults.splice(i, 1);
      }
    }
  };
  //Results
  for (var i = 0; i < data.data.length; i++) {

    if($('#french-btn').data("current") == 'en'){
      var downloadText = en.downloadBtn;
      var thumbUpText = "This is the correct result";
      var thumbDownText = "This is the wrong result";
    }else{
      var downloadText = fr.downloadBtn;
      var thumbUpText = "This is the correct result";
      var thumbDownText = "This is the wrong result";
    }
    var tempPDFName = data.data[i].pdf_url.split('/');
    var agreementNum = data.data[i].pdf_url.split('/').slice(-1)[0].split('.')[0];
    var finalAgg = agreementNum.substr(0,5) + "-" + agreementNum.substr(5,2);
    //Todo, set ID. return ID.
    $("#search-results").append("<div class='row search-result searchid-"+finalAgg+"' id='search-"+i+"' style='opacity:0; transform: translate(0px, 10px);'><div class='col s12'><div class='result-container'>"+
      "<div class='thumb-div' data-id='"+i+"'>"+
        "<a class='thumb-buttons thumb-up' data-position='top' data-delay='50' data-tooltip='"+thumbUpText+"' >"+
          //"<i class='material-icons light-green-text'>thumb_up</i>"+
          "<svg width='24' height='24' viewBox='0 0 24 24'><path fill='#aed581' d='M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-1.91l-.01-.01L23 10z'/></svg>"+
        "</a></br>"+
        "<a class='thumb-buttons thumb-down' data-position='bottom' data-delay='50' data-tooltip='"+thumbDownText+"' >"+
          "<svg width='24' height='24' viewBox='0 0 24 24'><path fill='#ef9a9a' d='M15 3H6c-.83 0-1.54.5-1.84 1.22l-3.02 7.05c-.09.23-.14.47-.14.73v1.91l.01.01L1 14c0 1.1.9 2 2 2h6.31l-.95 4.57-.03.32c0 .41.17.79.44 1.06L9.83 23l6.59-6.59c.36-.36.58-.86.58-1.41V5c0-1.1-.9-2-2-2zm4 0v12h4V3h-4z'/></svg>"+
          //"<i class='material-icons red-text text-lighten-2'>thumb_down</i>"+
        "</a>"+
      "</div>"+
      "<div class='result-title'>"+
        //"<a class='btn-flat waves-effect waves-grey lighten-2 download-btns' data-pdflink='"+data.data[i].pdf_url+"' data-position='top' data-delay='50' data-tooltip='"+downloadText+"' id='download-"+i+"'><i class='material-icons'>file_download</i></a>"+
      "</div>"+
      "<div class='result-pdf' data-pdflink='"+data.data[i].pdf_url+"' data-pdfmeta='"+data.data[i].metadata+"'>"+
        "<div class='metadata-div'></div>"+
        "<div class='pdf-icon-div'>"+
        '<svg x="0px" y="0px" width="45" height="45" viewBox="0 0 318.188 318.188"><g><polygon style="fill:#fff;" points="227.321,7.5 40.342,7.5 40.342,310.688 277.846,310.688 277.846,58.025"/><path style="fill:#FB3449;" d="M237.513,157.435c-3.644-6.493-16.231-8.533-22.006-9.451c-4.552-0.724-9.199-0.94-13.803-0.936c-3.615-0.024-7.177,0.154-10.693,0.354c-1.296,0.087-2.579,0.199-3.861,0.31c-1.314-1.36-2.584-2.765-3.813-4.202c-7.82-9.257-14.134-19.755-19.279-30.664c1.366-5.271,2.459-10.772,3.119-16.485c1.205-10.427,1.619-22.31-2.288-32.251c-1.349-3.431-4.946-7.608-9.096-5.528c-4.771,2.392-6.113,9.169-6.502,13.973c-0.313,3.883-0.094,7.776,0.558,11.594c0.664,3.844,1.733,7.494,2.897,11.139c1.086,3.342,2.283,6.658,3.588,9.943c-0.828,2.586-1.707,5.127-2.63,7.603c-2.152,5.643-4.479,11.003-6.717,16.161c-1.18,2.557-2.335,5.06-3.465,7.507c-3.576,7.855-7.458,15.566-11.814,23.021c-10.163,3.585-19.283,7.741-26.857,12.625c-4.063,2.625-7.652,5.476-10.641,8.603c-2.822,2.952-5.689,6.783-5.941,11.024c-0.141,2.394,0.807,4.717,2.768,6.137c2.697,2.015,6.271,1.881,9.4,1.226c10.25-2.15,18.121-10.961,24.824-18.387c4.617-5.115,9.872-11.61,15.369-19.465c0.012-0.018,0.024-0.036,0.037-0.054c9.428-2.923,19.689-5.391,30.579-7.205c4.975-0.825,10.082-1.5,15.291-1.974c3.663,3.431,7.621,6.555,11.938,9.164c3.363,2.069,6.94,3.816,10.684,5.119c3.786,1.237,7.595,2.247,11.528,2.886c1.986,0.284,4.017,0.413,6.092,0.334c4.631-0.175,11.278-1.951,11.714-7.57C238.627,160.265,238.256,158.757,237.513,157.435z M126.644,167.745c-2.169,3.36-4.261,6.382-6.232,9.041c-4.827,6.568-10.34,14.369-18.322,17.286c-1.516,0.554-3.512,1.126-5.616,1.002c-1.874-0.11-3.722-0.936-3.637-3.064c0.042-1.114,0.587-2.535,1.423-3.931c0.915-1.531,2.048-2.935,3.275-4.226c2.629-2.762,5.953-5.439,9.777-7.918c5.865-3.805,12.867-7.23,20.672-10.286C127.535,166.358,127.087,167.064,126.644,167.745z M153.866,83.485c-0.603-3.514-0.693-7.077-0.323-10.503c0.184-1.713,0.533-3.385,1.038-4.952c0.428-1.33,1.352-4.576,2.826-4.993c2.43-0.688,3.177,4.529,3.452,6.005c1.566,8.396,0.186,17.733-1.693,25.969c-0.299,1.31-0.632,2.599-0.973,3.883c-0.582-1.601-1.137-3.207-1.648-4.821C155.445,90.548,154.439,86.982,153.866,83.485z M170.549,149.765c-9.13,1.48-17.815,3.419-25.979,5.708c0.983-0.275,5.475-8.788,6.477-10.555c4.721-8.315,8.583-17.042,11.358-26.197c4.9,9.691,10.847,18.962,18.153,27.214c0.673,0.749,1.357,1.489,2.053,2.22C178.517,148.596,174.488,149.133,170.549,149.765zM232.293,161.459c-0.334,1.805-4.188,2.837-5.988,3.121c-5.316,0.836-10.94,0.167-16.028-1.542c-3.491-1.172-6.858-2.769-10.057-4.688c-3.18-1.921-6.155-4.181-8.936-6.673c3.429-0.206,6.9-0.341,10.388-0.275c3.488,0.035,7.003,0.211,10.475,0.665c6.511,0.726,13.807,2.961,18.932,7.186C232.088,160.085,232.41,160.821,232.293,161.459z"/><polygon style="fill:#FB3449;" points="235.14,32.763 40.342,32.763 40.342,7.5 227.321,7.5   "/><polygon style="fill:#D1D3D3;" points="227.321,58.025 277.846,58.025 227.321,7.5  "/>'+
        '<text style="fill:#555;" font-size="70" font-weight="600" x="68" y="255">OPEN</text><text style="fill:#555;" font-size="70" font-weight="600" x="100" y="308">PDF</text></g></svg>'+
        "</div>"+
        "<div class='result-pdf-page z-depth-4'>"+
          "<p class='blurry-text1'> Lorem Ipsum Dolor Sit Amet, Consectetur Adipiscing Elit. Nulla Lacinia, Urna Quis Pharetra Facilisis, Arcu Augue Pharetra Ligula Ac Laoreet Mauris.</p>"+
          "<div class='metadatalink'>Page <b>"+data.data[i].metadata.split('-')[1]+"</b></div><p class='result-text'>"+data.data[i].raw_passage+"</p>"+
          "<p class='blurry-text2'> Lorem Ipsum Dolor Sit Amet, Consectetur Adipiscing Elit. Nulla Lacinia, Urna Quis Pharetra Facilisis, Arcu Augue Pharetra Ligula, Ac Laoreet Mauris.</p>"+
        "</div>"+
        "<div class='inlinepdf'></div>"+
      "</div>"+
      ""+
      "</div></div></div>");
    //Set meta data link to correct position on left
    $("#search-"+i).transition({opacity:1, y:0, delay: 100 + i*250});
    //Highlight text
    for (var j = 0; j < highlightResults.length; j++) {
      var reg = new RegExp(highlightResults[j], 'gi');
      var text = $("#search-"+i).find('.result-text').html();
      var txt = text.replace(reg, function(str) {
        return "<span class='highlight'>" + str + "</span>";
      });
      $("#search-"+i).find('.result-text').html(txt);
    };
  }
  //click result to open up pdf.
  $(".pdf-icon-div").click(function (){
    //remove current pointer event.
    $(this).css('pointer-events','none');
    $(this).fadeOut();

    //window.open('/pdf/GraphBasics.pdf', '_blank');
    var $wordDiv = $(this).parent();
    var $pdfdiv = $(this).parent().find('.result-pdf-page');
    var $inlinepdf = $(this).parent().find('.inlinepdf');
    $wordDiv.attr('data-prevh',$wordDiv.height());
    $wordDiv.height($pdfdiv.outerHeight());

    $pdfdiv.fadeOut();
    $wordDiv.transition({height:($(window).height()-100)+'px', complete:function (){
      //set inlinepdf size;
      $inlinepdf.css('height', $(this).height()-40);
      $inlinepdf.css('width', $(this).width()-40);
      //current PDF;
      var pdflink = $(this).data('pdflink');
      var pdfmeta = $(this).data('pdfmeta').split('-');
      var $currentIframe = $("<embed>");
      var pdfoptions = "#pagemode=none&navpanes=0&toolbar=0&statusbar=0&zoom=80&page="+(parseInt(pdfmeta[1])+1);
      $currentIframe.css('height', $(this).height()-40);
      $currentIframe.css('width', $(this).width()-40);
      $currentIframe.attr('src',pdflink+pdfoptions);
      $currentIframe.attr('type','application/pdf');
      $inlinepdf.html($currentIframe);
    }});
    var pos = $wordDiv.offset().top -50;
    $('html, body').animate({scrollTop:pos},300);

    //Add close button.
    var $closebtn = $("<div>");
    $closebtn.addClass('closepdfbutton');
    $closebtn.width($wordDiv.width());
    $closebtn.text('Close PDF');
    $wordDiv.parent().append($closebtn);

    $closebtn.click(function (){
      var orgCont = $(this).parent().find('.result-pdf');
      orgCont.transition({height:orgCont.data('prevh')+'px', complete:function (){
        orgCont.find('.result-pdf-page').fadeIn();
        orgCont.parent().find('.pdf-icon-div').css('pointer-events','auto').fadeIn();

      }});
      orgCont.find('.inlinepdf').html("");
      $(this).remove();
    });
  });

  //download button event
  $(".download-btns").click(function (){
    var pdfLink = $(this).data('pdflink');
    window.open(pdfLink, '_blank');
  });
  $(".download-btns").tooltip({delay: 50}).each(function (){
    $("#"+$(this).data('tooltip-id')).css("margin-top", "16px").css("margin-left", "-8px");
  });

  //Thumb up or down
  $(".thumb-up").click(function (){
    $(this).parent().find('.thumb-down').removeClass('thumb-active');
    $(this).addClass('thumb-active');
    //Push new feedback
    var feedbackObj = {
      oid : $(this).parent().data('oid'),
      id : $(this).parent().data('id'),
      data : {
        raw_passage: data.data[$(this).parent().data('id')].raw_passage,
        metadata : data.data[$(this).parent().data('id')].metadata,
        pdf_url : data.data[$(this).parent().data('id')].pdf_url,
        query : data.query,
        feedback : true,
        date : new Date()
      }
    }
    socket.emit('feedbackSend', feedbackObj);
  });
  $(".thumb-up").tooltip({delay: 50}).each(function (i, obj){
    $(obj).css("margin-top", "16px");
  });

  $(".thumb-down").click(function (){
    $(this).parent().find('.thumb-up').removeClass('thumb-active');
    $(this).addClass('thumb-active');
    //Push new feedback
    var feedbackObj = {
      oid : $(this).parent().data('oid'),
      id : $(this).parent().data('id'),
      data : {
        raw_passage: data.data[$(this).parent().data('id')].raw_passage,
        metadata : data.data[$(this).parent().data('id')].metadata,
        pdf_url : data.data[$(this).parent().data('id')].pdf_url,
        query : data.query,
        feedback : false,
        date : new Date()
      }
    }
    socket.emit('feedbackSend', feedbackObj);
  });
  $(".thumb-down").tooltip({delay: 50}).each(function (i, obj){
    $(obj).css("margin-top", "0px");
  });

  //If still tutorial mode, show the next steps & change the buttons back.
  if(tutMode){
    closeTutorial();
    //first returned search.
    var fSearch = $("#search-results").find(".search-result")[0];
    if(fSearch){
      //title
      var tutTitle = $("<div>");
      tutTitle.addClass("floatingtext");
      tutTitle.html("The PDF title is shown here");
      tutTitle.css("margin-top","-33px");
      tutTitle.css("margin-left","30px");
      $(fSearch).append(tutTitle);

      //content
      var tutContent = $("<div>");
      tutContent.addClass("floatingtext");
      tutContent.html("The relevent PDF content is displayed here");
      tutContent.css("margin-top","60px");
      tutContent.css("margin-left","500px");
      $(fSearch).append(tutContent);

      //download
      var tutdown = $("<div>");
      tutdown.addClass("floatingtext");
      tutdown.html("Download the PDF here");
      tutdown.css("right","0");
      tutdown.css("margin-right","80px");
      $(fSearch).append(tutdown);

      //Thumbs
      var tutthumb = $("<div>");
      tutthumb.addClass("floatingtext");
      tutthumb.html("Use the thumbs up or down </br>to improve our search results");
      tutthumb.css("right","0");
      tutthumb.css("margin-right","-140px");
      tutthumb.css("margin-top","60px");
      $(fSearch).append(tutthumb);

      $(".floatingtext").click(function (){
        $(this).transition({
          opacity:0,
          y: -5,
          complete: function (){
            $(this).remove();
          }
        });
      });
    }
  }
});

socket.on('searchMeta', function (data){

  var maxWidth = $('.result-container').offset().left + $('.result-pdf-page')[0].offsetLeft - 40;
  $('.metadata-div').width(maxWidth);

  for (var i = 0; i < data.length; i++) {
    var $currentPDF = $('.searchid-'+data[i].agreementnumber);
    $currentPDF.find('.result-title').text("Agreement # " + data[i].agreementnumber);
    var $metadataDiv = $currentPDF.find('.metadata-div');

    //current agreement indicator
    if(data[i].currentagreementindicator == 'Current'){
      var $tempTag = $("<div>").addClass('metadata-tags green lighten-2 tooltipped').attr('data-tooltip',"Agreement Status").attr('data-position',"right").html(data[i].currentagreementindicator);
      $metadataDiv.append($tempTag);
    }else if(data[i].currentagreementindicator == 'Historical'){
      var $tempTag = $("<div>").addClass('metadata-tags red lighten-2 tooltipped').attr('data-tooltip',"Agreement Status").attr('data-position',"right").html(data[i].currentagreementindicator);
      $metadataDiv.append($tempTag);
    }else if(data[i].currentagreementindicator == 'Active'){
      var $tempTag = $("<div>").addClass('metadata-tags amber lighten-2 tooltipped').attr('data-tooltip',"Agreement Status").attr('data-position',"right").html(data[i].currentagreementindicator);
      $metadataDiv.append($tempTag);
    }
    $metadataDiv.append("<div class='float-clear'></div>");
    //company
    var $tempTag = $("<div>").addClass('metadata-tags tooltipped blue-grey lighten-4').attr('data-tooltip',"Company Name").attr('data-position',"right").html(data[i].companyofficialnameeng);
    $metadataDiv.append($tempTag);
    $metadataDiv.append("<div class='float-clear'></div>");
    //union
    var $tempTag = $("<div>").addClass('metadata-tags grey darken-3 white-text tooltipped').attr('data-tooltip',"Union Name").attr('data-position',"right").html(data[i].unionnameenglish);
    $metadataDiv.append($tempTag);
    $metadataDiv.append("<div class='float-clear'></div>");
    /*
    //Employees
    var $tempTag = $("<div>").addClass('metadata-tags blue-grey lighten-4 tooltipped').attr('data-tooltip',"# of Employees").attr('data-position',"bottom").html('<svg class="svg-person" width="15" height="15" viewBox="0 -2 18 18"><path d="M9 8c1.66 0 2.99-1.34 2.99-3S10.66 2 9 2C7.34 2 6 3.34 6 5s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V16h14v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>&nbsp;'+data[i].employeecount);
    $metadataDiv.append($tempTag);
    $metadataDiv.append("<div class='float-clear'></div>");
    //Dates
    var $tempTag = $("<div>").addClass('metadata-tags purple lighten-3 tooltipped').attr('data-tooltip',"Agreement Date").attr('data-position',"bottom").html('<svg width="15" height="15" viewBox="0 -2 24 24"><path d="M9 11H7v2h2v-2zm4 0h-2v2h2v-2zm4 0h-2v2h2v-2zm2-7h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V9h14v11z"/></svg>&nbsp;'+data[i].effectivedate+ ' ~ '+ data[i].expirydate);
    $metadataDiv.append($tempTag);
    $metadataDiv.append("<div class='float-clear'></div>");
    */
    $('.tooltipped').tooltip({delay: 50});
    //reset metadata position
    $metadataDiv.css('left', -$metadataDiv.width() + $metadataDiv.parent().find('.result-pdf-page')[0].offsetLeft+"px");
    //set the max width.
    //$metadataDiv.width(maxWidth);
  };
});

socket.on('autoComplete', function (data){
  $("#auto-complete").html("");
  if(data.length){
    $("#auto-complete").css("border-top", "1px solid #ddd");
  }else{
    $("#auto-complete").css("border-top", "none");
  }
  for (var i = 0; i < data.length; i++) {
    var addedP = $("<p>").attr("style","opacity:0; transform: translate(0px, 5px);").attr("data-uid",data[i]._id).text(data[i].searchStr);
    $("#auto-complete").append(addedP);
    addedP.transition({opacity:1, y:0});
  };

  //If one of the auto complete is clicked on.
  $("#auto-complete p").click(function (){
    $("#search-bar").val($(this).text());
    var e = jQuery.Event("keyup");
    e.which = 13;
    $("#search-bar").trigger(e);
    socket.emit('autoCompleteSelected', {selectedId: $(this).attr("data-uid")});
  });
});

socket.on('feedbackSaved', function (data){
  $(".thumb-div[data-id='"+data.id+"']").attr('data-oid',data.data._id);
});

socket.on('pdfNamesReturn', function (data){
  var resultArray = $("#filter-pdfname-input").val();
  $("#filter-pdfname-input option").each(function (i, opt){
    if(resultArray.indexOf($(opt).text()) == -1){
      $(opt).remove();
    }
  });
  var tempSearch = $(".chosen-search-input").val();
  for (var i = 0; i < data.length; i++) {
    $("#filter-pdfname-input").append('<option>'+data[i].agreementnumber+'</option>');
  };
  $("#filter-pdfname-input").trigger("chosen:updated");
  $(".chosen-search-input").val(tempSearch);
});