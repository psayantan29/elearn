from courses.forms import AddCourseForm
from courses.models import *
from .forms import *
from pinax.referrals.models import Referral
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import user_passes_test, login_required
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from itertools import chain
from django.http import Http404
from .models import UserProfile
import razorpay
import json

import logging

logger = logging.getLogger(__name__)


def home(request):
    context = {
        "title": "eLearning",
    }
    action = Referral.record_response(request, "login")
    
    respo=render(request, "home.html", context)
      
    if action is not None:
        referral = Referral.objects.get(id=action.referral.id)
        respo.set_cookie('parent',referral.user.username)
      

    return respo


def about(request):
    context = {
        "title": "About",
    }
    # tutorial  = request.COOKIES['parent']
    # print(tutorial) 
    return render(request, "users/about.html", context)


def faq(request):
    context = {
        "title": "faq",
    }
    # tutorial  = request.COOKIES['parent']
    # print(tutorial) 
    return render(request, "users/faq.html", context)   


def contact(request):
    contact_form = Contact(request.POST or None)

    context = {
        "title": "Contact",
        "contact_form": contact_form,
    }

    if contact_form.is_valid():
        sender = contact_form.cleaned_data.get("sender")
        subject = contact_form.cleaned_data.get("subject")
        from_email = contact_form.cleaned_data.get("email")
        message = contact_form.cleaned_data.get("message")
        message = 'Sender:  ' + sender + '\nFrom:  ' + from_email + '\n\n' + message
        send_mail(subject, message, settings.EMAIL_HOST_USER, [settings.EMAIL_HOST_USER], fail_silently=True)
        success_message = "We appreciate you contacting us, one of our Customer Service colleagues will get back" \
                          " to you within a 24 hours."
        messages.success(request, success_message)

        return redirect(reverse('contact'))

    return render(request, "users/contact.html", context)


@login_required
def profile(request):
    

    if request.user.is_site_admin:
        
        return redirect(reverse('admin'))

    elif request.user.is_professor:
        return redirect(reverse('professor'))
  

    return redirect(reverse('student'))
        

@login_required
def charged(request,course_name):
    razorpay_client = razorpay.Client(auth=("rzp_test_6ChBFF3DEQamI8", "RIn69McAqs35zFjHZOB0jqjM"))
    amount = 50000
    payment_id = request.POST['razorpay_payment_id']
    razorpay_client.payment.capture(payment_id, amount)
    c=Course.objects.get(course_name=course_name)
    c.students.set([request.user])
    # print(request)
    # print(c.students)
    # c.purchase()
    c.save()
    user=request.user
    if user.parent:
        user.parent.affamount=user.parent.affamount+1
        print(user.parent.affamount)
        user.parent.save()

    # print(c.students)
    # print("my name is Piyush \n")

    
    # return json.dumps(razorpay_client.payment.fetch(payment_id))
    
    return redirect('profile')

@login_required
def affiliate(request):
    
    profile = UserProfile.objects.get(username=request.user.username)
    # profile.parent = Profile.objects.get(user=referral.user)
    
          
    referral = Referral.create(
    user=profile,
    redirect_to=reverse("home")
    )
        
    profile.referral=referral
    profile.save()
    context={
        "profile":profile

    }
    
    return render(request, "users/affiliate.html",context)
    

@login_required
def charge(request,course_name):
    c=Course.objects.filter(course_name=course_name)
    print(c)
    q=c[0]
    print(q.text)
    print(q.students)
    # print(q.get("purchased"))
    # if q.get("purchased") == True:

    #     print("hi")
    #     return render(request,"courses/charged.html")
    user=request.user
    print(user.parent)
    context = {
           "title": "Courses",
            "user":user,
            "course":course_name,
            "intro":q,
            "text": q.text
            }
    
    return render(request, "courses/charge.html",context)

@user_passes_test(lambda user: user.is_site_admin)
def admin(request):
    add_user_form = AddUser(request.POST or None)
    queryset = UserProfile.objects.all()

    search = request.GET.get("search")
    if search:
        queryset = queryset.filter(username__icontains=search)

    context = {
        "title": "Admin",
        "add_user_form": add_user_form,
        "queryset": queryset,

    }

    if add_user_form.is_valid():
        instance = add_user_form.save(commit=False)
        passwd = add_user_form.cleaned_data.get("password")
        instance.password = make_password(password=passwd,
                                          salt='salt', )
        instance.save()
        reverse('profile')

    return render(request, "users/sysadmin_dashboard.html", context)


@user_passes_test(lambda user: user.is_professor)
def professor(request):
    add_course_form = AddCourseForm(request.POST or None)
    queryset_course = Course.objects.filter(user__username=request.user)

    context = {
        "title": "Professor",
        "add_course_form": add_course_form,
        "queryset_course": queryset_course,
    }

    if add_course_form.is_valid():
        course_name = add_course_form.cleaned_data.get("course_name")
        instance = add_course_form.save(commit=False)
        instance.user = request.user
        instance.text = add_course_form.cleaned_data.get("text")
        key = add_course_form.cleaned_data.get("link")

        if 'embed' not in key and 'youtube' in key:
            key = key.split('=')[1]
            instance.link = 'https://www.youtube.com/embed/' + key

        
        instance.save()
        return redirect(reverse('professor_course', kwargs={'course_name': course_name}))

    return render(request, "users/professor_dashboard.html", context)


@login_required
def student(request):
    queryset = Course.objects.filter(students=request.user)

    context = {
        "queryset": queryset,
        "title": request.user,
    }

    return render(request, "users/student_dashboard.html", context)


@user_passes_test(lambda user: user.is_site_admin)
def update_user(request, username):
    user = UserProfile.objects.get(username=username)
    data_dict = {'username': user.username, 'email': user.email}
    update_user_form = EditUser(initial=data_dict, instance=user)

    path = request.path.split('/')[1]
    redirect_path = path
    path = path.title()

    context = {
        "title": "Edit",
        "update_user_form": update_user_form,
        "path": path,
        "redirect_path": redirect_path,
    }

    if request.POST:
        user_form = EditUser(request.POST, instance=user)

        if user_form.is_valid():
            instance = user_form.save(commit=False)
            passwd = user_form.cleaned_data.get("password")

            if passwd:
                instance.password = make_password(password=passwd,
                                                  salt='salt', )
            instance.save()

            return redirect(reverse('profile'))

    return render(request, "users/edit_user.html", context)


@user_passes_test(lambda user: user.is_site_admin)
def delete_user(request, username):
    user = UserProfile.objects.get(username=username)
    user.delete()
    return redirect(reverse('profile'))


@login_required
def course_homepage(request, course_name):
    chapter_list = Chapter.objects.filter(course__course_name=course_name)
    for i in Course.objects.filter(students=request.user):
        if i.course_name == course_name:
            return redirect(reverse(student_course, kwargs={'course_name': course_name, "slug": chapter_list[0].slug}))
    if chapter_list:
        return redirect( reverse("charge") )
        # reverse(student_course, kwargs={'course_name': course_name, "slug": chapter_list[0].slug})
    else:
        warning_message = "Currently there are no videos for this webinar "
        messages.warning(request, warning_message)
        return redirect(reverse('courses'))


@login_required
def student_course(request, course_name, slug=None):
    course = Course.objects.get(course_name=course_name)
    chapter_list = Chapter.objects.filter(course=course)
    chapter = Chapter.objects.get(course__course_name=course_name, slug=slug)
    text = TextBlock.objects.filter(text_block_fk=chapter)
    videos = YTLink.objects.filter(yt_link_fk=chapter)
    files = FileUpload.objects.filter(file_fk=chapter)
    gdlinks = gdlink.objects.filter(gd_link_fk=chapter)
    user = request.user
    
    if user in course.students.all() or user.is_professor or user.is_site_admin or course.for_everybody:
        result_list = sorted(
            chain(text, videos, files, gdlinks),
            key=lambda instance: instance.date_created)

        context = {
            "course_name": course_name,
            "chapter_list": chapter_list,
            "chapter_name": chapter.chapter_name,
            "slug": chapter.slug,
            "result_list": result_list,
            "title": course_name + ' : ' + chapter.chapter_name,
        }
        # print(result_list)
        return render(request, "users/student_courses.html", context)

    else:
        raise Http404
