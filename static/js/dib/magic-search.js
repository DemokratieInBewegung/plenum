
Vue.component('dropdown', {
  props: ['options', 'selectedIdx'],
  components: {
    'dropdown-item': {
        props: ['title', 'selected'],
        computed: {
          itemClass: function(){
            return 'dropdown-item' + (this.selected ? ' active' : '');
          }
        }
      }
    }
});

Vue.component('search-bar', {
  props: ['filters', 'searchOptions'],
  data: function() {
    return { filters: this.filters,
             curText: '',
             focussed: false,
             selected: false,
             selectedIdx: -1,
           }
  },
  computed: {
    placeholder: function() {
      return this.selected
              ? (this.selected.placeholder || '')
              : ((this.filters && this.filters.length > 0)
                  ? ''
                  : 'Filtern und suchen...');
    },
    options: function(){

      let opts = this.selected ? ( this.selected.subSelection ? this.selected.subSelection : [] ) : this.searchOptions;
      if (this.curText) {
        let lowered_text = this.curText.toLowerCase();
        return opts.filter((x) => x.name.toLowerCase().indexOf(lowered_text) != -1)
      }
      return opts;
    },
    showList: function() {
      return this.focussed && this.options.length > 0;
    },
    searchCls: function() {
      return this.selected ? 'badge': '';
    }
  },
  methods: {
    add: function() {
      let msg = this.curText.trim()
      let select = this.selected ? this.selected : {'name': "Suche", 'key': 's'}
      if (msg) {
        this.filters.push({name: select.name, key: select.key , value: msg, label: msg});
        this.curText = '';
        this.selected = null;
        this.$refs.textInput.focus();
        this.trigger();
      }
    },
    remove: function(idx) {
      this.filters = this.filters.splice(idx, 1);
      Vue.nextTick(() => {
        this.trigger();
      });
    },
    select: function(item) {
      if (this.selected) {
        this.filters.push({
          name: this.selected.name,
          key: this.selected.key,
          value: item.value,
          label: item.name
        })
        this.selected = null;
        this.trigger();
      } else {
        this.selected = item;
      }
      this.curText = '';
      this.$refs.textInput.focus();
    },
    focus: function () {
      this.focussed = true;
    },
    blur: function () {
      this.focussed = false;
    },
    clear: function() {
      if (!this.selected) {
        this.focussed = false;
      } else {
        this.selected = null;
      }
    },
    down: function() {
      this.selectedIdx += 1;
    },
    up: function() {
      if (this.selectedIdx >= 0) {
        this.selectedIdx -= 1;
      }
    },
    trigger: function() {
      let query = this.filters.map(function(f, idx){
        return `${f.key}=${f.value}`
      }).join("&");
      ajaxGet('/?' + query)
    }
   }
});

var magicSearch = new Vue({
  el: '#magic-search',
  data: {
    filters: [],
    searchOptions: [
      {name: 'Bereich', key: 'b', placeholder: 'nach Bereichen filtern'},
      {name: 'Phase', key: 'f', placeholder: "nach Phase filtern", subSelection: [
        {name: 'In Vorbereitung', value: 'p'},
        {name: 'In Prüfung', value: 'i'},
        {name: 'Sucht Unterstützung', value: 's'},
        {name: 'In Diskussion', value: 'd'},
        {name: 'Finale Überarbeitung', value:'e'},
        {name: 'Finale Prüfung', value:'m'},
        {name: 'Abstimmung', value:'v'},
        {name: 'Angenommen', value:'a'},
        {name: 'Abgelehnt', value:'r'}
      ]},

      {name: 'Suche', key: 's', placeholder: 'nach Freitext suchen', showDevider: true},
    ]
  }
});
