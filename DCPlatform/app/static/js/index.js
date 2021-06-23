   $(document).ready(function() {
         $('#search_bar').select2({
               ajax: {
                 url: '/nlp_query',
                 delay: 250,
                 data: function (params) {
                   var res = {
                     query: params.term,
                   }

                   // Query parameters will be ?search=[term]&type=public
                   return res;
                 }
               },
             placeholder: "Поиск",
             allowClear: true,
             minimumInputLength: 3,
             language: "ru",
             disabled: true

         });

       $('#search_bar').on('select2:select', function (e) {
             var data = e.params.data;
             $('#tree').treeview('search', [ data.id, {
               revealResults: true,  // reveal matching nodes
             }]);
         });
       $.fn.select2.amd.define('select2/i18n/ru',[],function () {
         // Russian
         return {
             errorLoading: function () {
                 return 'Результат не может быть загружен.';
             },
             inputTooLong: function (args) {
                 var overChars = args.input.length - args.maximum;
                 var message = 'Пожалуйста, удалите ' + overChars + ' символ';
                 if (overChars >= 2 && overChars <= 4) {
                     message += 'а';
                 } else if (overChars >= 5) {
                     message += 'ов';
                 }
                 return message;
             },
             inputTooShort: function (args) {
                 var remainingChars = args.minimum - args.input.length;

                 var message = 'Пожалуйста, введите ' + remainingChars + ' или более символов';

                 return message;
             },
             loadingMore: function () {
                 return 'Загружаем ещё ресурсы…';
             },
             maximumSelected: function (args) {
                 var message = 'Вы можете выбрать ' + args.maximum + ' элемент';

                 if (args.maximum  >= 2 && args.maximum <= 4) {
                     message += 'а';
                 } else if (args.maximum >= 5) {
                     message += 'ов';
                 }

                 return message;
             },
             noResults: function () {
               return 'Ничего не найдено';
             },
             searching: function () {
               return 'Поиск…';
             }
         };
        });
   });
   $("#context-menu").on("click", function() {
   $(this).hide();
   });

   $("#context-menu").on("contextmenu", function(event) {
       event.preventDefault();
   $(this).hide();
   });


   var algoChosen = false;
   var dataLoaded = false;
   function ExpandTree() {
       let selected = $('#tree').treeview('getSelected')
       if (selected.length > 0) $('#tree').treeview('unselectNode',selected);
       $('#tree').treeview('expandAll');
   };

   function CollapseTree() {
       let selected = $('#tree').treeview('getSelected');
       if (selected.length > 0) $('#tree').treeview('unselectNode',selected);
       $('#tree').treeview('collapseAll');
   };

   function loadData(button)
   {
     file = button.files[0];
     const formData = new FormData()
     formData.append('file', file)

     fetch('load_data', {
         method: 'POST',
         body: formData,
     }).then(response => {
         $("#data_filename").text('Имя файла c данными: ' + file.name);
         dataLoaded = true;
         //runs_data
         if (algoChosen) {
             $("#bigRedButton").css('visibility', 'visible');
         }
     })
   }

   function selectOldData(label) {
        var e = document.getElementById("data_select");
        var data_id = e.value;
        fetch('select_old_data_' + data_id, {
         method: 'POST',
     }).then(response => {
         $("#data_filename").text('Имя файла c данными: ' + e.options[e.selectedIndex].text);
         dataLoaded = true;
         if (algoChosen) {
             $("#bigRedButton").css('visibility', 'visible');
         }
         return response.json()
     }).then(data => {
          clear_runs_table();
          console.log('run table cleared');
          for (let i = 0; i < data['runs_data'].length; i++) {
              let element =  data['runs_data'][i];
              insert_run(element[0], element[1], element[2], element[3]);
          }
        })
   }

   function downloadRes() {
         const a = document.createElement('a');
         a.download = '';
         a.href = '/get_res'
         a.click();
   }

   function loadTree(button)
   {
         file = button.files[0];
         var reader = new FileReader();
         reader.readAsText(file, "UTF-8");
         reader.onload = function (evt) {
             let json = JSON.stringify(evt.target.result);
             $.post('/tree', {
                 ont: json
             }).done(function(response) {
                 let selected = $('#tree').treeview('getSelected')
                 if (selected.length > 0) $('#tree').treeview('unselectNode',selected);
                 $('#tree').treeview('remove');
                 $('#tree').treeview({
                     data: response,
                     levels: 1,
                     onContextMenu: function(event, node) {
                         if (!node || node.state.disabled) return;
                         if (node.annotation) {
                             var top = event.pageY - 10;
                             var left = event.pageX - 90;
                             $('#annotationText').text(node.annotation);
                             $("#context-menu").css({
                                 display: "block",
                                 top: top,
                                 left: left
                             }).show();
                         }
                     }
                 })
                 $('.tree_opt').css('visibility', 'visible');
                 $("#ont_filename").text('Имя файла с онтологией: ' + file.name);
                 $("h1").text('Онтология загружена');
                 $("#ontLoadButton").text('Загрузить другую онтологию');
                 $('#search_bar').prop("disabled", false);
                 $('#tree').on('nodeSelected', onTreeSelect);
                 $('#tree').on('nodeUnselected', onTreeUnselect);
             }).fail(function() {
                $("h1").text("Произошла ошибка при обработке онтологии");
              });
         }
   }


   function onTreeUnselect(event, node) {
         $('#chosenNodeString').text('');
         $("#bigRedButton").css('visibility', 'hidden');
         $("#downloadResButton").css('visibility', 'hidden');
         $('#openModalButton').css('visibility', 'hidden');
         $('#search_bar').val(null).trigger('change');
         algoChosen = false;
   }

   function onTreeSelect(event, node) {
         $('#search_bar').val(null).trigger('change');
         $('#tree').treeview('clearSearch');
         var res = node.text;
         var selected = node;
         while (node.parentId || node.parentId > -1)
         {
             node = $('#tree').treeview('getParent', node);
             res = node.text + '->' + res;
         }
         $('#chosenNodeContainer').css('visibility', 'visible');
         $('#chosenNodeString').text(res);
         if (selected.isMethod) algoChosen = true;
         if (dataLoaded && algoChosen) {
             $("#bigRedButton").css('visibility', 'visible');
         }
   };
