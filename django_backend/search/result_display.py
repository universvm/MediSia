from medical_ir.search_type.search_module import *
from django.http import JsonResponse
import traceback
from django_redis import get_redis_connection
from config import settings

rconn = get_redis_connection("default")


def dispatcher(request):
    '''
    Put request parameters into the params attribute of request to facilitate subsequent processing.
    GET the parameter of Http request is in the url, which is obtained through the GET attribute of the request object.
    '''
    if request.method == 'GET':
        request.params = request.GET

    type = request.params['type']  # 'new' or 'follow up'
    if type == 'new':
        return new_search_result(request)
    elif type == 'follow-up':
        return followup_search_result(request)
    else:
        return JsonResponse(
            {'ret': 1, 'msg': 'This type of http request is not supported'})


search_module = SearchModule()
print('finish')


def new_search_result(request):
    """
    Receive HTTP request parameters and return the search result.

    Parameters
    ------------------------
    request: An object of HTTP request
    """

    try:
        query = request.params['query']
        if 'categories' in request.params:
            categories = eval(request.params['categories'])  # str list -> list
        else:
            categories = None

        if 'deep' in request.params:
            is_deep_search = eval(request.params['deep'])  # True or False
        else:
            is_deep_search = False

        cache_field = f"{query+str(is_deep_search)}"  # cache field

        if is_deep_search:
            cache_obj = rconn.hget(settings.CK.original_results,
                                   cache_field)

            # Firstly check whether the cache have the results corresponding to
            # the value

            if cache_obj:
                print('get cache')
                results = json.loads(cache_obj)
                pubyear_list, journal_list, categories_list, final_results = filter_pubyears_journals(
                    request, results)

            else:
                sorted_score, results = search_module.search(
                    query, categories, is_deep_search)
                pubyear_list, journal_list, categories_list, final_results = filter_pubyears_journals(
                    request, results)
                rconn.hset(
                    settings.CK.original_results,
                    cache_field,
                    json.dumps(results))

        elif is_deep_search == False:
            sorted_score, results = search_module.search(
                query, categories, is_deep_search)
            pubyear_list, journal_list, categories_list, final_results = filter_pubyears_journals(
                request, results)
            rconn.hset(
                settings.CK.original_results,
                cache_field,
                json.dumps(results))

        # 'total' specifies how much data there is in total
        return JsonResponse({'journals': journal_list,
                             'pubyears': pubyear_list,
                             'categories': categories_list,
                             'results': final_results})

    except BaseException:
        return JsonResponse(
            {'ret': 2, 'msg': f'unexpected error\n{traceback.format_exc()}'})


def followup_search_result(request):
    try:
        query = request.params['query']
        if 'categories' in request.params:
            categories = eval(request.params['categories'])  # str list
        else:
            categories = None

        if 'deep' in request.params:
            is_deep_search = eval(request.params['deep'])  # True or False
        else:
            is_deep_search = False

        # Firstly check whether the cache have the results corresponding to the
        # value
        cache_field = f"{query+str(is_deep_search)}"  # cache field

        cache_obj = rconn.hget(settings.CK.original_results,
                               cache_field)

        results = json.loads(cache_obj)

        # follow up search for categories
        if 'categories' in request.params:
            categories = eval(request.params['categories'])  # str list
            filtered_results = []
            for each_result in results:
                if each_result['category'] in categories:
                    filtered_results.append(each_result)
            pubyear_list, journal_list, categories_list, final_results = filter_pubyears_journals(
                request, filtered_results)
        else:
            pubyear_list, journal_list, categories_list, final_results = filter_pubyears_journals(
                request, results)

        return JsonResponse({'journals': journal_list,
                             'pubyears': pubyear_list,
                             'categories': categories_list,
                             'results': final_results})

    except BaseException:
        return JsonResponse(
            {'ret': 2, 'msg': f'unexpected error\n{traceback.format_exc()}'})


def filter_pubyears_journals(request, results):
    """
    Using FollowUpClass to get the list of jounals and pubyears and get the results filtered by specific journals or pubyears.

    Parameters
    ----------
    request:
        Http request
    results: original results searched by quesry
        List of dict [dict]

    Returns
    ----------
    date_index: dict
        {date: docid}
    journal_index: dict
        {journal: docid}
    final_results: Final results filtered by journals or pubyears
        List of dict [dict]

    """
    followup_search = FollowUpSearch(results)
    pubyears_list, journals_list, categories_list = followup_search.return_indeces()

    if 'journals' in request.params and 'pubyears' in request.params:
        journals = eval(request.params['journals'])
        temp_results = followup_search.search_journal(journals)
        # The list of pubyears only has 2 elements
        pubyears = eval(request.params['pubyears'])
        final_results = FollowUpSearch(
            temp_results).search_date(pubyears[0], pubyears[1])
        return pubyears_list, journals_list, categories_list, final_results
    elif 'journals' in request.params:
        journals = eval(request.params['journals'])  # str list
        final_results = followup_search.search_journal(journals)
        return pubyears_list, journals_list, categories_list, final_results
    elif 'pubyears' in request.params:
        # The list of pubyears only has 2 elements
        pubyears = eval(request.params['pubyears'])
        final_results = followup_search.search_date(pubyears[0], pubyears[1])
        return pubyears_list, journals_list, categories_list, final_results
    else:
        return pubyears_list, journals_list, categories_list, results
