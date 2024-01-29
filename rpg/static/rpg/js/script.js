


$(document).ready(function(){

    var templates = {
        thumbnailDefaultContainer: _.template(
        '<div class="thumbnailContainer col-lg-3 col-md-4 col-sm-6" data-number="<%= picNumber %>">' +
            '<div class="thumbnail">' +
                '<a href="#" class="btn btn-default addImage">'+
                    '<i class="fa fa-plus fa-5x"></i>'+
                '</a>'+
            '</div>'+
            '<input type="file" class="hidden" id="picture<%= picNumber %>" name="picture_<%= picNumber %>" />' +
        '</div>'),
        thumbnailFilled: _.template(
        '<div class="thumbnail">' +
            '<div class="caption">' +
                '<div class="btn-group-container">' +
                    '<div class="btn-group btn-group-xs" role="group">' +
                        '<button type="button" class="btn btn-default favorize" title="Als Anzeigebild wählen"><i class="fa fa-heart"></i></button>' +
                        '<button type="button" class="btn btn-default remove" title="Bild löschen"><i class="fa fa-minus"></i></button>' +
                    '</div>' +
                '</div>' +
            '</div>' +
            '<div class="addImage">' +
                '<img src="<%= imgSource %>" />' +
            '</div>' +
        '</div>'),
        dropdownImage: _.template(
        '<li>' +
            '<div class="miniImageContainer">' +
                '<span class="helper"></span>' +
                '<a class="aligned selectable-pic" href="#" data-picture="<%= picId %>"><img data-dest="<%= pictureName %>" src="<%= staticUrl %><%= pictureName %>" /></a>' +
            '</div>' +
        '<li>'),
        bigImage: _.template('<img class="aligned" src="<%= staticUrl %><%= pictureName %>" />')
    }

    var openFilechooser = function(e){
        e.preventDefault();
        console.log("fired");
        var $t = $(e.currentTarget);
        $t.parent().parent().find('input[type=file]').trigger('click');
    };

    var renderThumbnailDefaultContainer = function(number){
        return templates.thumbnailDefaultContainer({picNumber: number})
    };

    var renderThumbnailFilled = function(source){
        return templates.thumbnailFilled({imgSource:source});
    };

    var putImageToGalery = function(e){
        var $t = $(e.currentTarget);
        var $container = $t.parent();
        var $row = $t.parent().parent();
        var highestNumber = parseInt($row.find('.thumbnailContainer').last().data().number);
        var currentNumber = parseInt($container.data().number);
        if ($t[0].files && $t[0].files[0]){
            var reader = new FileReader();
            reader.onload = function(ev){
                $container.find('div.thumbnail').replaceWith(renderThumbnailFilled(ev.target.result));
                if ($row.find('i.fa-plus')==null || $row.find('i.fa-plus')[0]==null){
                    $row.append(renderThumbnailDefaultContainer(highestNumber + 1));
                }
            };
            reader.readAsDataURL($t[0].files[0]);
        } else {
            if (highestNumber == currentNumber){
                $container.replaceWith(renderThumbnailDefaultContainer(currentNumber));
            } else {
                $container.remove();
            }
        }
    };

    var removeImageFromGalery = function(e){
        var $t = $(e.currentTarget);
        var $container = $t.parents('div.thumbnailContainer');
        $container.remove();
    }

    var favorizePicture = function(e){
        var $t = $(e.currentTarget);
        var $newImage = $t.parents('.thumbnailContainer').first().find('input[type=file]');
        var $existingImage = $t.parents('.thumbnailContainer').first().find('input[id^=existing_picture_]')
        var newPic = newPic;
        if ($newImage.length) {
            newPic = $newImage.attr('name')
        } else if ($existingImage.length) {
            newPic = $existingImage.val()
        }
        var isFavorit = false;
        if ($t.hasClass("btn-danger")) {
            isFavorit = true;
        }
        $('button.favorize').removeClass("btn-danger").addClass("btn-default").attr('title', 'Als Anzeigebild wählen');
        $('#favorite').val('')
        if (!isFavorit){
            $t.removeClass("btn-default").addClass("btn-danger").attr('title', 'Als Anzeigebild abwählen');
            $('#favorite').val(newPic)
        }
    }

    var keepRelationsPlausible = function() {
        $('.relation-role li').show();
        $('input[id^=relationTarget]').each(function(i1, relTarg){
            var $relTarg = $(relTarg);
            if ($relTarg.val()) {
                $('.relation-role li a[data-value='+$relTarg.val()+']')
                .filter(function() {
                    return $(this).parents('tr').find('input[id^=relationTarget]').val() !== $relTarg.val();
                })
                .parents('li').hide();
            }
        });
        $('.relation-role ul.dropdown-menu').last().filter(function(){
            return $(this).find('li').filter(function(){ return $(this).css('display') !== 'none'; }).length < 2;
        }).parents('[id^=relationContainer]').hide();
        configureAddRemoveRelationButtons()
    }

    var configureAddRemoveRelationButtons = function() {
        var $empty = $('input[id^=relationT]').filter(function() {
            return $(this).val() === "" && $(this).parents('[id^=relationContainer]').is(':visible');
        });
        if ($empty.length === 0 && $('tr[id^=relationContainer]:visible').length
                < $('.relation-role ul.dropdown-menu').first().find('li a').length-1) {
            $('.addRelation').removeClass('disabled');
        } else {
            $('.addRelation').addClass('disabled');
        }
        if ($('.newRelation').length > 1) {
            $('.newRelation .removeRelation').removeClass('disabled');
        } else {
            $('.newRelation .removeRelation').addClass('disabled');
        }
    }

    var chooseDropdownItem = function(e) {
        e.preventDefault();
        var $t = $(e.currentTarget);
        var $displayTarget = $t.parents('.dropdown').first().find('.dropdown-chosen');
        var $dataTarget = $t.parents('.dropdown').first().find('input');
        $displayTarget.empty().append($t.html());
        $dataTarget.val($t.data('value'));
        if ($t.hasClass('relation-item')) {
            keepRelationsPlausible();
        }
        $('.dropdown.open .dropdown-toggle').dropdown('toggle');
        return false;
    }

    var addRelation = function(e) {
        e.preventDefault();
        var $t = $(e.currentTarget);
        var $lastRelation = $('[id^=relationContainer]').last();
        if ($lastRelation.is(':hidden')) {
            $lastRelation.show();
            return false;
        }
        var $new = $lastRelation.clone();
        var lastIteration = parseInt($lastRelation.attr('id').split('Container')[1]);
        var newIteration = lastIteration + 1;
        $new.attr('id', 'relationContainer' + newIteration);
        $new.find('input').each(function(ind, elm) {
            var $elm = $(elm);
            $elm.attr('id', $elm.attr('id').replace(lastIteration, newIteration));
            $elm.attr('name', $elm.attr('name').replace(lastIteration, newIteration));
            $elm.val('');
        })
        $new.find('.dropdown-chosen').empty();
        $new.insertAfter($lastRelation);
        keepRelationsPlausible();
        return false;
    }

    var removeRelation = function(e) {
        e.preventDefault();
        var $t = $(e.currentTarget);
        $t.parents('tr').first().remove();
        keepRelationsPlausible();
        return false;
    }

    var goToWidgetTarget = function(e) {
        var $t = $(e.target);
        while (!$t.is('[data-url]')) {
            $t = $t.parent()
        }
        window.location = $t.data('url');
    }

    var changeRoleType = function(e) {
        var $t = $(e.currentTarget);
        if ($t.val() == 'fixed') {
            $('#sideRoleConfig').hide();
            $('#sideRoleConfig input').val('');
            $('#roleConfig').show();
        } else if ($t.val() == 'custom') {
            $('#roleConfig').hide();
            $('#rolePic').hide();
            $('#rolePic input').val('');
            $('#roleConfig select').val('');
            $('#sideRoleConfig').show();
        }
    }

    var changeRole = function(e) {
        var $t = $(e.currentTarget);
        var $urlRoot = $t.data('url');
        if ($t.val()) {
            var favFound = false;
            var data = {
                role_id: $t.val(),
            }
            $.get($t.data('url'), data, function(d) {
                var $picSelect = $('#rolePic ul.image-dropdown');
                $picSelect.empty();
                $('#rolePic .bigImageContainer img').remove();
                if (d.pics && d.pics.length > 0) {
                    $.each(d.pics, function(i, e) {
                        $picSelect.append(templates.dropdownImage({
                            staticUrl:$t.data('static'),
                            pictureName: e.dest,
                            picId: e.id
                        }));
                        if (!$('#rolePic input').data('dest') && e.fav) {
                            $('#rolePic .bigImageContainer').append(templates.bigImage({
                                staticUrl:$t.data('static'),
                                pictureName: e.dest
                            }));
                            $('#rolePic input').val(e.id);
                            favFound = true;
                        }
                    });
                    if ($('#rolePic input').data('dest')) {
                        $('#rolePic .bigImageContainer').append(templates.bigImage({
                            staticUrl:$t.data('static'),
                            pictureName:$('#rolePic input').data('dest')
                        }));
                    } else if (!favFound) {
                        var randomPic = d.pics[Math.floor(Math.random() * d.pics.length)];
                        $('#rolePic .bigImageContainer').append(templates.bigImage({
                            staticUrl:$t.data('static'),
                            pictureName: randomPic.dest
                        }));
                        $('#rolePic input').val(randomPic.id);
                    }
                    $('#rolePic').show();
                } else {
                    $('#rolePic').hide();
                    $('#rolePic input').val('');
                }
            });
        } else {
            $('#rolePic').hide();
            $('#rolePic input').val('');
        }
    }

    var selectPic = function(e) {
        var $t = $(e.currentTarget);
        $('#rolePic input').val($t.data('picture'));
        $('#rolePic input').removeData('dest');
        selectPictureWithDest($t.find('img').data('dest'))
        $('#rolePic .dropdown-toggle').dropdown('toggle');
        return false;
    }

    var selectPictureWithDest = function(dest) {
        var static = $('[data-static]').data('static');
        $('#rolePic .bigImageContainer img').remove();
        $('#rolePic .bigImageContainer').append(templates.bigImage({
            staticUrl: static,
            pictureName: dest
        }));
    }

    $('.datepickerContainer input').datepicker({
        format: "dd.mm.yyyy",
        startDate: "01.01.0000"
    });

    $('div.color').click(function(e){
        var $t = $(e.currentTarget);
        $t.parents('.btn-group')[0].find('.glyphicon-text-color').css('color', $t.css('background-color'));
        $('#text').focus();
    });

    $('div.colorpicker').html('<a href="#" id="ff0000" class="color" style="background-color:#ff0000;"></a><a href="#" id="ff4444" class="color" style="background-color:#ff4444;"></a><a href="#" id="ff8888" class="color" style="background-color:#ff8888;"></a><a href="#" id="ffbbbb" class="color" style="background-color:#ffbbbb;"></a><a href="#" id="ff8800" class="color" style="background-color:#ff8800;"></a><a href="#" id="ffa844" class="color" style="background-color:#ffa844;"></a><a href="#" id="ffc888" class="color" style="background-color:#ffc888;"></a><a href="#" id="ffd8bb" class="color" style="background-color:#ffd8bb;"></a><a href="#" id="ffff00" class="color" style="background-color:#ffff00;"></a><a href="#" id="ffff44" class="color" style="background-color:#ffff44;"></a><a href="#" id="ffff88" class="color" style="background-color:#ffff88;"></a><a href="#" id="ffffbb" class="color" style="background-color:#ffffbb;"></a><a href="#" id="88ff00" class="color" style="background-color:#88ff00;"></a><a href="#" id="a8ff44" class="color" style="background-color:#a8ff44;"></a><a href="#" id="c8ff88" class="color" style="background-color:#c8ff88;"></a><a href="#" id="d8ffbb" class="color" style="background-color:#d8ffbb;"></a><a href="#" id="00ff00" class="color" style="background-color:#00ff00;"></a><a href="#" id="44ff44" class="color" style="background-color:#44ff44;"></a><a href="#" id="88ff88" class="color" style="background-color:#88ff88;"></a><a href="#" id="bbffbb" class="color" style="background-color:#bbffbb;"></a><a href="#" id="00ff88" class="color" style="background-color:#00ff88;"></a><a href="#" id="44ffa8" class="color" style="background-color:#44ffa8;"></a><a href="#" id="88ffc8" class="color" style="background-color:#88ffc8;"></a><a href="#" id="bbffd8" class="color" style="background-color:#bbffd8;"></a><a href="#" id="00ffff" class="color" style="background-color:#00ffff;"></a><a href="#" id="44ffff" class="color" style="background-color:#44ffff;"></a><a href="#" id="88ffff" class="color" style="background-color:#88ffff;"></a><a href="#" id="bbffff" class="color" style="background-color:#bbffff;"></a><a href="#" id="0088ff" class="color" style="background-color:#0088ff;"></a><a href="#" id="44a8ff" class="color" style="background-color:#44a8ff;"></a><a href="#" id="88c8ff" class="color" style="background-color:#88c8ff;"></a><a href="#" id="bbd8ff" class="color" style="background-color:#bbd8ff;"></a><a href="#" id="0000ff" class="color" style="background-color:#0000ff;"></a><a href="#" id="4444ff" class="color" style="background-color:#4444ff;"></a><a href="#" id="8888ff" class="color" style="background-color:#8888ff;"></a><a href="#" id="bbbbff" class="color" style="background-color:#bbbbff;"></a><a href="#" id="8800ff" class="color" style="background-color:#8800ff;"></a><a href="#" id="a844ff" class="color" style="background-color:#a844ff;"></a><a href="#" id="c888ff" class="color" style="background-color:#c888ff;"></a><a href="#" id="d8bbff" class="color" style="background-color:#d8bbff;"></a><a href="#" id="ff00ff" class="color" style="background-color:#ff00ff;"></a><a href="#" id="ff44ff" class="color" style="background-color:#ff44ff;"></a><a href="#" id="ff88ff" class="color" style="background-color:#ff88ff;"></a><a href="#" id="ffbbff" class="color" style="background-color:#ffbbff;"></a><a href="#" id="ff0088" class="color" style="background-color:#ff0088;"></a><a href="#" id="ff44a8" class="color" style="background-color:#ff44a8;"></a><a href="#" id="ff88c8" class="color" style="background-color:#ff88c8;"></a><a href="#" id="ffbbd8" class="color" style="background-color:#ffbbd8;"></a><a href="#" id="111111" class="color" style="background-color:#111111;"></a><a href="#" id="333333" class="color" style="background-color:#333333;"></a><a href="#" id="555555" class="color" style="background-color:#555555;"></a><a href="#" id="777777" class="color" style="background-color:#777777;"></a><a href="#" id="999999" class="color" style="background-color:#999999;"></a><a href="#" id="bbbbbb" class="color" style="background-color:#bbbbbb;"></a><a href="#" id="dddddd" class="color" style="background-color:#dddddd;"></a><a href="#" id="ffffff" class="color" style="background-color:#ffffff;"></a>');

    $('#postType').change(function(e){
        var $t = $(e.currentTarget);
        if ($t.val()=="post"){
            $('#postData').removeClass('hidden');
        } else {
            $('#postData').addClass('hidden');
        }
    });

    $('#role').change(function(e){
        var $t = $(e.currentTarget);
        if (!$t.val()){
            $('#roleName').prop('disabled', false);
        } else {
            $('#roleName').prop('disabled', true);
        }
    });

    $('#doneImages').click(function(e){
        var $t = $(e.currentTarget);
        var $pics = $t.parents('.modal-content').find('img');
        if ($pics.parents('.modal-content').find('.btn-danger').length>0){
            var $container = $pics.parents('.modal-content').find('.btn-danger').parents('.thumbnailContainer');
        } else if ($pics.length > 0) {
            var totalNumber = $pics.length;
            var randomNumber = Math.floor(Math.random()*totalNumber);
            var $container = $pics.eq(randomNumber).parents('.thumbnailContainer');
        } else {
            var $container = $('.thumbnailContainer');
        }
        var $imgDisp = $('.img-display').parent();
        var f = $container.find('input[type=file]');
        var newF = f.clone();
        newF.attr('name', 'displayPic')
        newF.attr('id', 'displayPic');
        if ($container.find('img').length>0){
            $imgDisp.find('img').attr('src', $container.find('img').attr('src'));
        } else {
            $imgDisp.find('img').attr('src', '');
        }
        if ($imgDisp.find('input[type=file]').length==0){
            $imgDisp.append(newF);
        } else {
            $imgDisp.find('input[type=file]').replaceWith(newF);
        }
        return true;
    });

    $('body').on('click', '.thumbnailContainer a.addImage', openFilechooser);

    $('body').on('change', '.thumbnailContainer input[type=file]', putImageToGalery);

    $('body').on('click', '.thumbnailContainer button.remove', removeImageFromGalery);

    $('body').on('click', '.thumbnailContainer button.favorize', favorizePicture);

    $('body').on('click', '.dropdown-item', chooseDropdownItem);

    $('body').on('click', '.addRelation', addRelation);
    $('body').on('click', '.removeRelation', removeRelation);
    keepRelationsPlausible();

    $('#postType').trigger('change');
    $('#role').trigger('change');
    $('div.datepickerContainer').filter(function() { return $(this).find('input#born, input#died')}).on('click', function(e) {
        var $t = $(e.currentTarget);
        $t.find('input').prop('disabled', false);
        $t.find('input').focus();
    });
    $('input#born, input#died').on('blur', function(e) {
        var $t = $(e.currentTarget);
        setTimeout(function() {
            if ($t.val() === "") {
                $t.prop('disabled', true);
            }
        }, 300);
    });

    $('.widget').on('click', goToWidgetTarget);

    $('.summernote').summernote({
        height: 500,
        toolbar: [
            ['style', ['bold', 'italic', 'clear']],
            ['color', ['color']]
        ]
    });
    $('.summernote').summernote('foreColor', '#c8c8c8');
    $('.summernote').summernote('backColor', 'transparent');
    $('.note-color .note-palette').first().remove();
    $('.note-color-reset').removeClass('btn-light').addClass('btn-default');
    $('.note-statusbar').hide();

    $('#roleStatus input').on('change', changeRoleType)
    $('#roleStatus input:checked').trigger('change')

    $('select[name=role]').on('change', changeRole)
    $('select[name=role]').trigger('change')

    $('body').on('click', 'a.selectable-pic', selectPic)

    $('#commentModal').on('show.bs.modal', function(e) {
        var $button = $(e.relatedTarget);
        var action = $button.data('action');
        var type = $button.data('type');
        var modal = $(this);
        modal.find('form').attr('action', action);
        modal.find('input#type').val(type);
        modal.find('textarea').val('');
    });

});