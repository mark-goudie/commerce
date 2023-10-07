from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db.models import Max
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import User, Listing, Bid, Comment, Category
from .forms import ListingForm


def index(request):
    active_listings = Listing.objects.filter(active=True)
    return render(request, "auctions/index.html", {"active_listings": active_listings})


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


def create_listing(request):
    # Check if the user is authenticated
    if not request.user.is_authenticated:
        # assuming 'login' is the name of your login view
        return redirect('login')

    if request.method == 'POST':
        form = ListingForm(request.POST)
        if form.is_valid():
            new_listing = form.save(commit=False)
            new_listing.owner = request.user
            new_listing.current_bid = new_listing.starting_bid
            new_listing.save()
            return redirect('listing_detail', listing_id=new_listing.id)

    else:
        form = ListingForm()

    return render(request, 'auctions/create_listing.html', {'form': form})


def listing_detail(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    current_bid = Bid.objects.filter(
        listing=listing).aggregate(Max("amount"))["amount__max"]

    return render(request, "auctions/listing_detail.html", {
        "listing": listing,
        "current_bid": current_bid,
        "user_watchlist": listing.watchlist_items.filter(id=request.user.id),
    })


def watchlist(request):
    # Check if the user is authenticated
    if not request.user.is_authenticated:
        # assuming 'login' is the name of your login view
        return redirect('login')

    user = request.user
    watchlist_items = user.watchlisted_listings.filter(active=True)
    return render(request, "auctions/watchlist.html", {"watchlist_items": watchlist_items})


def category_list(request):
    categories = Category.objects.all()
    return render(request, "auctions/category_list.html", {"categories": categories})


def category_listings(request, category_id):
    category = Category.objects.get(id=category_id)
    listings = Listing.objects.filter(category=category, active=True)
    return render(request, "auctions/category_listings.html", {"category": category, "listings": listings})


def add_comment(request, listing_id):
    if request.method == "POST":
        content = request.POST.get("comment_text")
        listing = get_object_or_404(Listing, id=listing_id)
        comment = Comment.objects.create(
            listing=listing, commenter=request.user, content=content)
        comment.save()
        messages.success(request, "Comment added successfully!")
        return redirect('listing_detail', listing_id=listing_id)
    else:
        messages.error(request, "Error adding comment!")
        return redirect('listing_detail', listing_id=listing_id)


def place_bid(request, listing_id):
    if not request.user.is_authenticated:
        messages.error(request, "You need to be logged in to place a bid.")
        return redirect('login')

    listing = get_object_or_404(Listing, id=listing_id)

    if request.method == "POST":
        bid_amount = float(request.POST.get("bid_amount"))

        if (listing.current_bid and bid_amount > listing.current_bid) or (not listing.current_bid and bid_amount > listing.starting_bid):
            Bid.objects.create(
                listing=listing, user=request.user, amount=bid_amount)
            listing.current_bid = bid_amount
            # Assuming you have a current_bidder field in Listing model
            listing.current_bidder = request.user
            listing.save()
        else:
            messages.warning(
                request, "Your bid must be higher than the current bid.")

        return redirect('listing_detail', listing_id=listing.id)


def watchlist_toggle(request, listing_id):
    user = request.user
    listing = get_object_or_404(Listing, id=listing_id)

    if listing.watchlist_items.filter(id=user.id).exists():
        # If listing is already in user's watchlist, remove it
        listing.watchlist_items.remove(user)
        messages.success(request, "Listing removed from watchlist!")
    else:
        # Otherwise, add it to the watchlist
        listing.watchlist_items.add(user)
        messages.success(request, "Listing added to watchlist!")

    return redirect('listing_detail', listing_id=listing.id)


def close_auction(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    listing.active = False
    listing.save()
    messages.success(request, "Auction closed!")
    return redirect('listing_detail', listing_id=listing.id)
