# Standard Python Library imports.
from functools import reduce
import operator

# Core Django imports.
from django.contrib import messages
from django.db.models import Q
from django.views.generic import (
    DetailView,
    ListView,
)

# Blog application imports.
from blog.models.article_models import Article
from blog.models.category_models import Category
from blog.forms.blog.comment_forms import CommentForm


class ArticleListView(ListView):
    context_object_name = "articles"
    paginate_by = 12
    queryset = Article.objects.filter(status=Article.PUBLISHED, deleted=False)
    template_name = "blog/article/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(approved=True)
        return context


class ArticleDetailView(DetailView):
    model = Article
    template_name = 'blog/article/article_detail.html'

    def get_context_data(self, **kwargs):
        session_key = f"viewed_article {self.object.slug}"
        if not self.request.session.get(session_key, False):
            self.object.views += 1
            self.object.save()
            self.request.session[session_key] = True

        kwargs['related_articles'] = \
            Article.objects.filter(category=self.object.category, status=Article.PUBLISHED).order_by('?')[:3]
        kwargs['article'] = self.object
        kwargs['comment_form'] = CommentForm()
        return super().get_context_data(**kwargs)


class ArticleSearchListView(ListView):
    model = Article
    paginate_by = 12
    context_object_name = 'search_results'
    template_name = "blog/article/article_search_list.html"

    def get_queryset(self):
        """
         Busque una entrada de usuario en la barra de búsqueda.

         Pasa el valor de la consulta a la vista de búsqueda usando el parámetro 'q'.
         Luego, en la vista, busca los campos 'título', 'babosa', 'cuerpo' y.

         Para que la búsqueda sea un poco más inteligente, digamos que alguien busca
         'container docker ansible' y quiere buscar los registros donde todos
         Aparecen 3 palabras en el contenido del artículo en cualquier orden, divide la consulta
         en palabras separadas y encadenarlas.        
         """

        query = self.request.GET.get('q')

        if query:
            query_list = query.split()
            search_results = Article.objects.filter(
                reduce(operator.and_,
                       (Q(title__icontains=q) for q in query_list)) |
                reduce(operator.and_,
                       (Q(slug__icontains=q) for q in query_list)) |
                reduce(operator.and_,
                       (Q(body__icontains=q) for q in query_list))
            )

            if not search_results:
                messages.info(self.request, f"No results for '{query}'")
                return search_results.filter(status=Article.PUBLISHED, deleted=False)
            else:
                messages.success(self.request, f"Results for '{query}'")
                return search_results.filter(status=Article.PUBLISHED, deleted=False)
        else:
            messages.error(self.request, f"Lo sentimos, no ingresó ninguna palabra clave")
            return []

    def get_context_data(self, **kwargs):
        """
            Agregar categorías a los datos de contexto.
        """
        context = super(ArticleSearchListView, self).get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(approved=True)
        return context


class TagArticlesListView(ListView):
    """
        Listar artículos relacionados con una etiqueta.
    """
    model = Article
    paginate_by = 12
    context_object_name = 'tag_articles_list'
    template_name = 'blog/article/tag_articles_list.html'

    def get_queryset(self):
        """
            Filtrar artículos por tag_name
        """

        tag_name = self.kwargs.get('tag_name', '')

        if tag_name:
            tag_articles_list = Article.objects.filter(tags__name__in=[tag_name],
                                                       status=Article.PUBLISHED,
                                                       deleted=False
                                                       )

            if not tag_articles_list:
                messages.info(self.request, f"No hay resultados para la etiqueta '{tag_name}'")
                return tag_articles_list
            else:
                messages.success(self.request, f"Resultados para la etiqueta '{tag_name}'")
                return tag_articles_list
        else:
            messages.error(self.request, "Etiqueta no válida")
            return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(approved=True)
        return context
