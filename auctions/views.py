from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse

from .models import User, Listing, Bid, Comment, Watchlist, Category
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

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
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
    if request.method == 'POST':
        form = ListingForm(request.POST)
        if form.is_valid():
            new_listing = form.save(commit=False)
            new_listing.owner = request.user
            new_listing.save()
            return redirect('listings')
    else:
        form = ListingForm()

    return render(request, 'auctions/create_listing.html', {'form': form})


def listing_detail(request, listing_id):
    try:
        listing = Listing.objects.get(pk=listing_id)
    except Listing.DoesNotExist:
        return HttpResponseBadRequest("Listing not found")

    current_bid = Bid.objects.filter(
        listing=listing).aggregate(Max("amount"))["amount__max"]

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "watchlist_toggle":
            Watchlist.toggle_watchlist(request.user, listing)
        elif action == "place_bid":
            bid_amount = float(request.POST.get("bid_amount"))
            if current_bid is None or bid_amount > current_bid:
                Bid.objects.create(
                    listing=listing, user=request.user, amount=bid_amount)
                listing.current_price = bid_amount
                listing.save()
            else:
                return HttpResponseBadRequest("Invalid bid amount")
        elif action == "close_auction":
            if request.user == listing.owner and listing.is_active:
                winning_bid = Bid.objects.filter(
                    listing=listing).order_by("-amount").first()
                if winning_bid:
                    listing.winner = winning_bid.user
                    listing.is_active = False
                    listing.save()
        elif action == "add_comment":
            comment_text = request.POST.get("comment_text")
            Comment.objects.create(
                listing=listing, user=request.user, text=comment_text)

    return render(request, "auctions/listing_detail.html", {
        "listing": listing,
        "current_bid": current_bid,
        "user_watchlist": listing.watchlist.filter(user=request.user),
    })


def watchlist(request):
    user = request.user
    watchlist_items = user.watchlist.all()
    return render(request, "auctions/watchlist.html", {"watchlist_items": watchlist_items})


def category_list(request):
    categories = Category.objects.all()
    return render(request, "auctions/category_list.html", {"categories": categories})


def category_listings(request, category_id):
    category = Category.objects.get(id=category_id)
    listings = Listing.objects.filter(category=category, closed=False)
    return render(request, "auctions/category_listings.html", {"category": category, "listings": listings})
