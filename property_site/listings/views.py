from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
import datetime
from django.db.models import Q, Sum, Avg, Count, Subquery, OuterRef
from django.db.models.functions import TruncMonth
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib import messages
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_POST
from .models import Property, Agent, Conversation, Message
from .templatetags.listing_extras import display_name
from .forms import PropertyForm, AgentCreateForm

def index(request):
    properties = Property.objects.all()

    # Search by title or location
    q = request.GET.get('q', '').strip()
    if q:
        properties = properties.filter(Q(title__icontains=q) | Q(location__icontains=q))

    # Minimum bedrooms
    bedrooms = request.GET.get('bedrooms', '')
    if bedrooms.isdigit():
        properties = properties.filter(bedrooms__gte=int(bedrooms))

    # Sorting (newest first by default)
    order = {'low_price': 'price', 'high_price': '-price'}.get(request.GET.get('sort'), '-created_at')
    properties = properties.order_by(order)

    # Check if the logged-in user has an 'agent' profile connected to them
    is_agent = False
    if request.user.is_authenticated and hasattr(request.user, 'agent'):
        is_agent = True

    # Pass the properties to the index.html template
    context = {
        'properties': properties,
        'is_agent': is_agent
    }
    return render(request, 'listings/index.html', context)

def property_detail(request, pk):
    # Fetch the specific property by its Primary Key (ID), or return a 404 error if not found
    property_obj = get_object_or_404(Property, pk=pk)

    # SECURITY CHECK: Determine if the logged-in user is allowed to edit/delete this property
    can_edit = False
    if request.user.is_authenticated and hasattr(request.user, 'agent'):
        if property_obj.agent == request.user.agent:
            can_edit = True

    # Pass this specific property and the permission flag to the detail template
    chat = None
    if request.user.is_authenticated:
        chat = Conversation.objects.filter(property=property_obj, client=request.user).first()

    context = {
        'property': property_obj,
        'can_edit': can_edit,
        'chat': chat,
    }
    return render(request, 'listings/property_detail.html', context)

# Add this new view at the bottom of the file
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Automatically log the user in after they register
            login(request, user)
            return redirect('listings:index')
    else:
        form = UserCreationForm()

    return render(request, 'registration/register.html', {'form': form})

# Add this new restricted view at the very bottom
@login_required
def create_listing(request):
    # SECURITY CHECK: If the user is NOT an agent, completely deny access!
    if not hasattr(request.user, 'agent'):
        raise PermissionDenied("Access Denied: Only registered Agents can create property listings.")

    if request.method == 'POST':
        # request.FILES is required for processing image uploads
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            # commit=False creates the object but doesn't save to the database yet
            property_obj = form.save(commit=False)

            # Automatically set the listing's agent to the currently logged-in agent
            property_obj.agent = request.user.agent

            # Now save it to the database
            property_obj.save()
            return redirect('listings:property_detail', pk=property_obj.pk)
    else:
        form = PropertyForm()

    return render(request, 'listings/create_listing.html', {'form': form})

# Add these two new restricted views at the very bottom
@login_required
def edit_listing(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)

    # SECURITY CHECK: Deny access if not an agent OR if the agent doesn't own this listing
    if not hasattr(request.user, 'agent') or property_obj.agent != request.user.agent:
        raise PermissionDenied("Access Denied: You can only edit properties that you created.")

    if request.method == 'POST':
        # instance=property_obj tells the form to update the existing record, not create a new one
        form = PropertyForm(request.POST, request.FILES, instance=property_obj)
        if form.is_valid():
            form.save()
            return redirect('listings:property_detail', pk=property_obj.pk)
    else:
        # Pre-fill the form with the existing data
        form = PropertyForm(instance=property_obj)

    return render(request, 'listings/edit_listing.html', {'form': form, 'property': property_obj})

@login_required
def delete_listing(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)

    # SECURITY CHECK: Deny access if not an agent OR if the agent doesn't own this listing
    if not hasattr(request.user, 'agent') or property_obj.agent != request.user.agent:
        raise PermissionDenied("Access Denied: You can only delete properties that you created.")

    if request.method == 'POST':
        property_obj.delete()
        return redirect('listings:index')

    return render(request, 'listings/delete_listing.html', {'property': property_obj})


@login_required
def dashboard(request):
    # Agents see their own listings; other users see the whole site
    agent = getattr(request.user, 'agent', None)
    qs = Property.objects.filter(agent=agent) if agent else Property.objects.all()

    month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    totals = qs.aggregate(total=Count('id'), value=Sum('price'), avg=Avg('price'))

    type_names = dict(Property.PROPERTY_TYPES)
    months = list(qs.annotate(m=TruncMonth('created_at')).values('m').annotate(n=Count('id')).order_by('m'))[-6:]
    recent_prices = list(qs.order_by('-created_at')[:12])[::-1]

    charts = {
        'months': [{'l': r['m'].strftime('%b'), 'v': r['n']} for r in months],
        'types': [{'l': type_names.get(r['property_type'], r['property_type']), 'v': r['n']}
                  for r in qs.values('property_type').annotate(n=Count('id'))],
        'prices': [{'l': p.title, 'v': float(p.price)} for p in recent_prices],
    }

    context = {
        'agent': agent,
        'scope': 'Your listings' if agent else 'All listings',
        'total': totals['total'],
        'value': totals['value'] or 0,
        'avg': totals['avg'] or 0,
        'new_this_month': qs.filter(created_at__gte=month_start).count(),
        'members': User.objects.count(),
        'agents': Agent.objects.count(),
        'featured': qs.order_by('-price').first(),
        'recent': qs.order_by('-created_at')[:6],
        'charts': charts,
        'is_agent': agent is not None,
    }
    return render(request, 'listings/dashboard.html', context)


def _superuser_only(user):
    if not user.is_superuser:
        raise PermissionDenied("Access Denied: only a superuser can manage users and agents.")


def _users_page(request, form):
    users = (User.objects.select_related('agent')
             .annotate(n=Count('agent__properties'))
             .order_by('-is_superuser', '-is_staff', 'username'))
    return render(request, 'listings/manage_users.html', {
        'users': users, 'form': form,
        'is_agent': hasattr(request.user, 'agent'),
    })


@login_required
def manage_users(request):
    _superuser_only(request.user)
    return _users_page(request, AgentCreateForm())


@login_required
@require_POST
def add_agent(request):
    _superuser_only(request.user)
    form = AgentCreateForm(request.POST)
    if form.is_valid():
        agent = form.save()
        messages.success(request, f"Agent account created for {agent.user.get_full_name()}.")
        return redirect('listings:manage_users')
    return _users_page(request, form)


@login_required
@require_POST
def user_action(request, pk, action):
    _superuser_only(request.user)
    target = get_object_or_404(User, pk=pk)
    name = target.get_full_name() or target.username

    if target.is_superuser and not request.user.is_superuser:
        raise PermissionDenied("Only a superuser can change a superuser account.")

    if action == 'make_agent':
        phone = request.POST.get('phone_number', '').strip()
        if not phone:
            messages.error(request, "Enter a phone number to make someone an agent.")
        else:
            Agent.objects.get_or_create(user=target, defaults={'phone_number': phone})
            messages.success(request, f"{name} is now an agent.")

    elif action == 'remove_agent':
        agent = getattr(target, 'agent', None)
        count = agent.properties.count() if agent else 0
        if count:
            # Agent.properties uses CASCADE, so deleting would wipe their listings
            messages.error(request, f"{name} still has {count} listing(s). Delete or reassign them first.")
        elif agent:
            agent.delete()
            messages.success(request, f"{name} is no longer an agent.")

    elif action == 'toggle_active':
        if target == request.user:
            messages.error(request, "You can't disable your own account.")
        else:
            target.is_active = not target.is_active
            target.save(update_fields=['is_active'])
            messages.success(request, f"{name} is now {'active' if target.is_active else 'disabled'}.")
    else:
        raise Http404("Unknown action")

    return redirect('listings:manage_users')


# ---------------- Tour requests and chat ----------------

def _chat_or_403(request, pk):
    chat = get_object_or_404(Conversation.objects.select_related('property', 'client', 'agent__user'), pk=pk)
    if request.user.id not in (chat.client_id, chat.agent.user_id):
        raise PermissionDenied("This conversation is private.")
    return chat


@login_required
@require_POST
def book_tour(request, pk):
    prop = get_object_or_404(Property.objects.select_related('agent__user'), pk=pk)
    if prop.agent.user_id == request.user.id:
        messages.error(request, "You can't book a tour on your own listing.")
        return redirect('listings:property_detail', pk=prop.pk)

    note = request.POST.get('note', '').strip()[:1000]
    try:
        date = datetime.date.fromisoformat(request.POST.get('preferred_date', ''))
    except ValueError:
        date = None

    chat, created = Conversation.objects.get_or_create(
        property=prop, client=request.user,
        defaults={'agent': prop.agent, 'preferred_date': date})
    if not created:                      # a repeat request re-opens the conversation
        chat.status = 'pending'
        chat.preferred_date = date or chat.preferred_date
        chat.save(update_fields=['status', 'preferred_date', 'updated_at'])

    text = "Tour request" + (f" for {date:%d %b %Y}" if date else "") + "."
    if note:
        text += "\n" + note
    Message.objects.create(conversation=chat, sender=request.user, body=text)
    messages.success(request, "Tour request sent. The agent has been notified; you can chat here.")
    return redirect('listings:conversation', pk=chat.pk)


@login_required
def inbox(request):
    last = Message.objects.filter(conversation=OuterRef('pk')).order_by('-created_at').values('body')[:1]
    chats = list(Conversation.objects
                 .filter(Q(client=request.user) | Q(agent__user=request.user))
                 .select_related('property', 'client', 'agent__user')
                 .annotate(unread=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user)),
                           last_body=Subquery(last)))
    for c in chats:
        c.other = c.agent.user if request.user.id == c.client_id else c.client
    return render(request, 'listings/inbox.html', {'chats': chats, 'is_agent': hasattr(request.user, 'agent')})


@login_required
def conversation(request, pk):
    chat = _chat_or_403(request, pk)
    if request.method == 'POST':
        body = request.POST.get('body', '').strip()[:2000]
        if body:
            Message.objects.create(conversation=chat, sender=request.user, body=body)
            chat.save(update_fields=['updated_at'])
        return redirect('listings:conversation', pk=chat.pk)

    chat.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    thread = list(chat.messages.select_related('sender'))
    as_agent = request.user.id == chat.agent.user_id
    return render(request, 'listings/conversation.html', {
        'chat': chat, 'thread': thread, 'as_agent': as_agent,
        'other': chat.client if as_agent else chat.agent.user,
        'last_id': thread[-1].id if thread else 0,
    })


@login_required
def chat_poll(request, pk):
    chat = _chat_or_403(request, pk)
    after = request.GET.get('after', '0')
    after = int(after) if after.isdigit() else 0
    new = list(chat.messages.filter(id__gt=after).select_related('sender'))
    chat.messages.filter(id__gt=after, is_read=False).exclude(sender=request.user).update(is_read=True)
    return JsonResponse({
        'status': chat.status,
        'messages': [{'id': m.id, 'mine': m.sender_id == request.user.id, 'name': display_name(m.sender),
                      'body': m.body, 'time': timezone.localtime(m.created_at).strftime('%d %b, %H:%M')} for m in new],
    })


@login_required
@require_POST
def tour_response(request, pk, decision):
    chat = _chat_or_403(request, pk)
    if request.user.id != chat.agent.user_id:
        raise PermissionDenied("Only the listing's agent can respond to a tour request.")
    if decision not in ('confirm', 'decline'):
        raise Http404("Unknown response")
    chat.status = 'confirmed' if decision == 'confirm' else 'declined'
    chat.save(update_fields=['status', 'updated_at'])
    when = f" for {chat.preferred_date:%d %b %Y}" if chat.preferred_date else ""
    text = (f"Your tour{when} is confirmed. Message me here if anything changes."
            if decision == 'confirm' else
            f"Sorry, I can't do the tour{when}. Message me and we can find another time.")
    Message.objects.create(conversation=chat, sender=request.user, body=text)
    return redirect('listings:conversation', pk=chat.pk)
